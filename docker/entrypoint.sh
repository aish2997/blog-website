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

# Always run collectstatic to ensure we have the latest static files
# The --clear flag ensures old files are removed
echo "Collecting static files (including Django admin)..."
python manage.py collectstatic --noinput --clear || {
    echo "⚠️ WARNING: Failed to collect static files. Admin panel may not render correctly."
    echo "Checking staticfiles directory..."
    ls -la /app/staticfiles/ 2>/dev/null || echo "staticfiles directory not found"
}

# Verify admin static files were collected
if [ -d "/app/staticfiles/admin" ]; then
    echo "✅ Django admin static files found in /app/staticfiles/admin"
    echo "  - CSS files: $(find /app/staticfiles/admin/css -name "*.css" 2>/dev/null | wc -l)"
    echo "  - JS files: $(find /app/staticfiles/admin/js -name "*.js" 2>/dev/null | wc -l)"
else
    echo "❌ WARNING: Django admin static files NOT found! Admin panel will not render correctly."
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