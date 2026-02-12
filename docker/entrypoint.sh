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

# Pre-flight: check critical env vars are set (print name + length, never values)
echo "=== Pre-flight Environment Check ==="
for var_name in SECRET_KEY DATABASE_URL ALLOWED_HOSTS DJANGO_SETTINGS_MODULE; do
    eval var_value=\$$var_name
    if [ -n "$var_value" ]; then
        echo "OK: $var_name is set (${#var_value} chars)"
    else
        echo "MISSING: $var_name"
    fi
done
echo "====================================="

# Pre-flight: test Django settings import with full error capture
echo "Testing Django settings import..."
python -c "
from django.conf import settings
_ = settings.SECRET_KEY  # force lazy settings to load
print('OK: Django settings imported successfully')
" 2>&1 || {
    echo "FATAL: Django settings failed to load. See error above."
    exit 1
}

# Detect database type
if [ -n "$DATABASE_URL" ]; then
    echo "✅ PostgreSQL database detected (DATABASE_URL is set)"
    echo "Database: ${DATABASE_URL%%:*}  # Show only the protocol part for security"
    USE_POSTGRESQL=true
else
    echo "⚠️  SQLite database mode (DATABASE_URL not set)"
    echo "For production, it's recommended to use PostgreSQL via DATABASE_URL"
    USE_POSTGRESQL=false
    DATABASE_PATH=${DATABASE_PATH:-/tmp/db.sqlite3}
fi

# Validate Django configuration
echo "Validating Django configuration..."
python manage.py check --deploy 2>&1 || {
    echo "⚠️ Django check reported issues (non-fatal)"
}

# Database initialization - different logic for PostgreSQL vs SQLite
if [ "$USE_POSTGRESQL" = true ]; then
    echo "Running database migrations for PostgreSQL..."
    python manage.py migrate --noinput || {
        echo "❌ ERROR: Database migrations failed!"
        echo "Check DATABASE_URL and ensure PostgreSQL is accessible"
        exit 1
    }

    # Clean orphaned comments (PostgreSQL only - safe to run)
    echo "Cleaning orphaned comments..."
    python manage.py clean_orphaned_comments 2>&1 || {
        echo "Note: Orphaned comments cleanup completed or not needed"
    }
else
    # SQLite-specific logic (backup/restore)
    # Try to restore database from GCS first (if configured)
    if [ -n "$GCS_BUCKET_MEDIA" ]; then
        echo "Attempting to restore database from GCS..."
        python manage.py sync_database --action restore 2>&1 || {
            echo "Note: Database restore failed or no backup exists (normal for first deployment)"
        }
    fi

    # Check if database exists after restore attempt
    if [ ! -f "$DATABASE_PATH" ]; then
        echo "Database not found. Creating new database at $DATABASE_PATH"
        python manage.py migrate --noinput
    else
        echo "Database found at $DATABASE_PATH"
        echo "Checking for new migrations..."
        python manage.py migrate --noinput
    fi
fi

# ALWAYS check for superuser and create if missing (handles ephemeral database issue)
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ] && [ -n "$DJANGO_SUPERUSER_EMAIL" ]; then
    echo "Ensuring admin superuser exists..."

    # Use a Python script that reads credentials from environment variables directly
    # This prevents credentials from appearing in process listings or shell history
    SUPERUSER_CREATED=$(python manage.py shell -c "
import os
import sys
from django.contrib.auth import get_user_model

User = get_user_model()
username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

if not all([username, email, password]):
    print('error: missing credentials', file=sys.stderr)
    sys.exit(1)

try:
    if User.objects.filter(username=username).exists():
        print('exists')
    else:
        User.objects.create_superuser(
            username=username,
            email=email,
            password=password
        )
        print('created')
except Exception as e:
    print(f'error: {e}', file=sys.stderr)
    sys.exit(1)
")

    if [ "$SUPERUSER_CREATED" = "created" ]; then
        echo "✅ Superuser created successfully"

        # Backup database after creating superuser (SQLite only)
        if [ "$USE_POSTGRESQL" = false ] && [ -n "$GCS_BUCKET_MEDIA" ]; then
            echo "Backing up database with new superuser to GCS..."
            python manage.py sync_database --action backup --force 2>&1 || {
                echo "Warning: Backup after superuser creation failed"
            }
        fi
    elif [ "$SUPERUSER_CREATED" = "exists" ]; then
        echo "✅ Superuser already exists"
    else
        echo "⚠️  Warning: Could not verify/create superuser"
    fi
else
    echo "⚠️  Admin credentials not provided via Secret Manager. Admin panel will not be accessible."
    echo "   Configure these secrets in Google Secret Manager:"
    echo "   - django-superuser-username-{environment}"
    echo "   - django-superuser-password-{environment}"
    echo "   - django-superuser-email-{environment}"
fi

# Final backup to ensure latest state is saved (SQLite only)
if [ "$USE_POSTGRESQL" = false ] && [ -n "$GCS_BUCKET_MEDIA" ]; then
    echo "Performing final database backup to GCS..."
    python manage.py sync_database --action backup 2>&1 || {
        echo "Note: Final backup skipped (database may be unchanged)"
    }
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

# Start periodic database backup in background (SQLite only - every 30 minutes)
if [ "$USE_POSTGRESQL" = false ] && [ -n "$GCS_BUCKET_MEDIA" ]; then
    echo "Starting periodic database backup service (SQLite)..."
    (
        while true; do
            sleep 1800  # 30 minutes
            echo "[$(date)] Running scheduled database backup..."
            python manage.py sync_database --action backup 2>&1 | tee -a /tmp/db_backup.log
        done
    ) &
    BACKUP_PID=$!
    echo "Database backup service started with PID: $BACKUP_PID"
else
    echo "PostgreSQL mode: Periodic backup service not needed (database is persistent)"
fi

echo "Starting Gunicorn..."

# Trap signals to ensure backup process is cleaned up (if it exists)
if [ -n "$BACKUP_PID" ]; then
    trap "kill $BACKUP_PID 2>/dev/null" EXIT
fi

# Start the application with gunicorn
# Configuration depends on database type
if [ "$USE_POSTGRESQL" = true ]; then
    # PostgreSQL: Can handle multiple workers and threads efficiently
    echo "Starting Gunicorn with PostgreSQL-optimized configuration (4 workers, 4 threads)..."
    exec gunicorn --bind :$PORT \
        --workers 4 \
        --threads 4 \
        --timeout 120 \
        --access-logfile - \
        --error-logfile - \
        --log-level info \
        portfolio.wsgi:application
else
    # SQLite: Limited to 1 worker for write safety
    echo "Starting Gunicorn with SQLite-compatible configuration (1 worker, 2 threads)..."
    exec gunicorn --bind :$PORT \
        --workers 1 \
        --threads 2 \
        --timeout 120 \
        --access-logfile - \
        --error-logfile - \
        --log-level info \
        portfolio.wsgi:application
fi