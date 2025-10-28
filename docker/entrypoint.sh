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

    # Create superuser if credentials are provided (from Secret Manager)
    if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ] && [ -n "$DJANGO_SUPERUSER_EMAIL" ]; then
        echo "Checking for admin superuser..."

        # Use a Python script for safer credential handling
        python manage.py shell -c "
from django.contrib.auth import get_user_model
import sys

User = get_user_model()
username = '$DJANGO_SUPERUSER_USERNAME'

try:
    if User.objects.filter(username=username).exists():
        print(f'✅ Superuser {username} already exists')
    else:
        # Create the superuser
        User.objects.create_superuser(
            username=username,
            email='$DJANGO_SUPERUSER_EMAIL',
            password='$DJANGO_SUPERUSER_PASSWORD'
        )
        print(f'✅ Superuser {username} created successfully')
except Exception as e:
    print(f'❌ Error creating superuser: {e}', file=sys.stderr)
    # Don't exit - let the app run but log the error
"
    else
        echo "ℹ️  Admin credentials not provided via Secret Manager. Skipping superuser creation."
        echo "   To enable automatic admin creation, configure the following secrets in Google Secret Manager:"
        echo "   - django-superuser-username"
        echo "   - django-superuser-password"
        echo "   - django-superuser-email"
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

# Verify static files (already collected during Docker build)
echo "Verifying static files configuration..."
echo "STATIC_ROOT: /app/staticfiles"
echo "STATIC_URL: ${STATIC_URL:-/static/}"

# Verify admin static files exist (they should have been collected during Docker build)
if [ -d "/app/staticfiles/admin" ]; then
    echo "✅ Django admin static files found in /app/staticfiles/admin"
    echo "  - CSS files: $(find /app/staticfiles/admin/css -name "*.css" 2>/dev/null | wc -l)"
    echo "  - JS files: $(find /app/staticfiles/admin/js -name "*.js" 2>/dev/null | wc -l)"

    # Verify critical admin files exist
    if [ -f "/app/staticfiles/admin/css/base.css" ]; then
        echo "✅ Critical admin CSS file (base.css) verified"
    else
        echo "❌ ERROR: Critical admin CSS file (base.css) is missing!"
        echo "Admin panel will not render correctly. Check Docker build logs."
        # Don't exit - let the app run but log the error
    fi
else
    echo "❌ ERROR: Django admin static files NOT found in /app/staticfiles/admin!"
    echo "Admin panel will not render correctly. This should have been fixed during Docker build."
    echo "Check the Docker build logs for collectstatic errors."
    # Don't exit - let the app run but log the error
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