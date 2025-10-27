#!/bin/bash
# Remove set -e to prevent script from exiting on first error

echo "Starting Django application initialization..."

# Debug environment variables
echo "=== Environment Variables Debug ==="
echo "DJANGO_SETTINGS_MODULE: ${DJANGO_SETTINGS_MODULE}"
echo "DEBUG: ${DEBUG}"
echo "ALLOWED_HOSTS: ${ALLOWED_HOSTS}"
echo "CLOUD_RUN_SERVICE_URL: ${CLOUD_RUN_SERVICE_URL:-Not set, using wildcard CSRF patterns}"
echo "GCS_BUCKET_MEDIA: ${GCS_BUCKET_MEDIA}"
echo "GCS_BUCKET_STATIC: ${GCS_BUCKET_STATIC}"
echo "K_SERVICE (Cloud Run): ${K_SERVICE:-Not running on Cloud Run}"
echo "=================================="

# Validate Django configuration
echo "Validating Django configuration..."
python manage.py check --deploy 2>&1 || {
    echo "⚠️ Django check reported issues (non-fatal)"
}

# Database path from environment or default
DATABASE_PATH=${DATABASE_PATH:-/tmp/db.sqlite3}

# Try to restore database from GCS first (if configured)
if [ -n "$GCS_BUCKET_MEDIA" ]; then
    echo "Attempting to restore database from GCS..."
    python manage.py sync_database --action restore 2>&1 || {
        echo "Warning: Database restore failed or skipped (this is normal on first deployment)"
    }
fi

# Check if database exists after restore attempt
if [ ! -f "$DATABASE_PATH" ]; then
    echo "Database not found. Creating new database at $DATABASE_PATH"

    # Run migrations to create database schema
    echo "Running database migrations..."
    python manage.py migrate --noinput

    # Create superuser if credentials are provided
    if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ] && [ -n "$DJANGO_SUPERUSER_EMAIL" ]; then
        echo "Creating superuser..."
        python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='$DJANGO_SUPERUSER_USERNAME').exists():
    User.objects.create_superuser('$DJANGO_SUPERUSER_USERNAME', '$DJANGO_SUPERUSER_EMAIL', '$DJANGO_SUPERUSER_PASSWORD')
    print('Superuser created successfully')
else:
    print('Superuser already exists')
"
    fi

    # Backup the newly created database to GCS
    if [ -n "$GCS_BUCKET_MEDIA" ]; then
        echo "Backing up new database to GCS..."
        python manage.py sync_database --action backup --force 2>&1 || {
            echo "Warning: Initial backup failed (check GCS permissions)"
        }
    fi
else
    echo "Database found at $DATABASE_PATH"

    # Still run migrations in case there are new ones
    echo "Checking for new migrations..."
    python manage.py migrate --noinput

    # Backup database after migrations
    if [ -n "$GCS_BUCKET_MEDIA" ]; then
        echo "Backing up database to GCS after migrations..."
        python manage.py sync_database --action backup 2>&1 || {
            echo "Warning: Post-migration backup skipped"
        }
    fi
fi

# Check and collect static files
echo "Checking static files configuration..."
echo "STATIC_ROOT: /app/staticfiles"
echo "STATIC_URL: ${STATIC_URL:-/static/}"
echo "GCS_BUCKET_STATIC: ${GCS_BUCKET_STATIC:-Not set, using WhiteNoise}"

# Ensure staticfiles directory exists with proper permissions
mkdir -p /app/staticfiles
chmod 755 /app/staticfiles

# Clear the staticfiles directory first to ensure clean state
echo "Clearing old static files..."
rm -rf /app/staticfiles/*

# Always run collectstatic to ensure we have the latest static files
echo "Collecting static files (including Django admin)..."
python manage.py collectstatic --noinput --verbosity 2 2>&1 | tee /tmp/collectstatic.log

# Check if collectstatic succeeded
if [ ${PIPESTATUS[0]} -eq 0 ]; then
    echo "✅ Static files collected successfully"
else
    echo "❌ ERROR: Failed to collect static files. Admin panel will not render correctly."
    echo "Collectstatic log:"
    tail -20 /tmp/collectstatic.log
fi

# Verify admin static files were collected
if [ -d "/app/staticfiles/admin" ]; then
    echo "✅ Django admin static files found in /app/staticfiles/admin"
    echo "  - CSS files: $(find /app/staticfiles/admin/css -name "*.css" 2>/dev/null | wc -l)"
    echo "  - JS files: $(find /app/staticfiles/admin/js -name "*.js" 2>/dev/null | wc -l)"
    echo "  - Image files: $(find /app/staticfiles/admin/img -name "*" -type f 2>/dev/null | wc -l)"

    # List some key admin CSS files to verify
    echo "Key admin CSS files:"
    ls -la /app/staticfiles/admin/css/base.css 2>/dev/null || echo "  - base.css not found"
    ls -la /app/staticfiles/admin/css/dashboard.css 2>/dev/null || echo "  - dashboard.css not found"
    ls -la /app/staticfiles/admin/css/login.css 2>/dev/null || echo "  - login.css not found"
else
    echo "❌ WARNING: Django admin static files NOT found! Admin panel will not render correctly."
    echo "Checking if Django admin is installed:"
    python -c "import django.contrib.admin; print('Django admin module found')" || echo "Django admin module NOT found"
fi

# Check total number of static files collected
TOTAL_FILES=$(find /app/staticfiles -type f 2>/dev/null | wc -l)
echo "Total static files collected: $TOTAL_FILES"

# Verify WhiteNoise can serve static files (only if not using GCS)
if [ -z "$GCS_BUCKET_STATIC" ]; then
    echo "Testing WhiteNoise static file serving..."
    python -c "
from django.conf import settings
import os

print('STORAGES config:', settings.STORAGES.get('staticfiles'))
print('STATIC_ROOT:', settings.STATIC_ROOT)
print('STATIC_ROOT exists:', os.path.exists(settings.STATIC_ROOT))
print('Admin static path:', os.path.join(settings.STATIC_ROOT, 'admin'))
print('Admin static exists:', os.path.exists(os.path.join(settings.STATIC_ROOT, 'admin')))
" 2>&1 || echo "Could not verify WhiteNoise configuration"
fi

echo "Initialization complete."

# Initialize BACKUP_PID as empty
BACKUP_PID=""

# Start periodic database backup in background (every 30 minutes)
if [ -n "$GCS_BUCKET_MEDIA" ]; then
    echo "Starting periodic database backup service..."
    (
        while true; do
            sleep 1800  # 30 minutes
            echo "[$(date)] Running scheduled database backup..."
            python manage.py sync_database --action backup 2>&1 | tee -a /tmp/db_backup.log
        done
    ) &
    BACKUP_PID=$!
    echo "Database backup service started with PID: $BACKUP_PID"
fi

echo "Starting Gunicorn..."

# Trap signals to ensure backup process is cleaned up (if it exists)
if [ -n "$BACKUP_PID" ]; then
    trap "kill $BACKUP_PID 2>/dev/null" EXIT
fi

# Start the application with gunicorn
# Using 1 worker for SQLite compatibility (SQLite doesn't handle concurrent writes well)
# Reduced threads to prevent SQLite lock issues
exec gunicorn --bind :$PORT \
    --workers 1 \
    --threads 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    portfolio.wsgi:application