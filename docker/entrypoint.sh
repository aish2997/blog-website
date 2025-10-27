#!/bin/bash
set -e

echo "Starting Django application initialization..."

# Database path from environment or default
DATABASE_PATH=${DATABASE_PATH:-/tmp/db.sqlite3}

# Try to restore database from GCS first
if [ -n "$GCS_BUCKET_MEDIA" ]; then
    echo "Attempting to restore database from GCS..."
    python manage.py sync_database --action restore || echo "Database restore skipped or failed"
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
        python manage.py sync_database --action backup --force || echo "Initial backup failed"
    fi
else
    echo "Database found at $DATABASE_PATH"

    # Still run migrations in case there are new ones
    echo "Checking for new migrations..."
    python manage.py migrate --noinput

    # Backup database after migrations
    if [ -n "$GCS_BUCKET_MEDIA" ]; then
        echo "Backing up database to GCS after migrations..."
        python manage.py sync_database --action backup || echo "Post-migration backup skipped"
    fi
fi

# Collect static files if not already done
if [ ! -d "staticfiles" ] || [ -z "$(ls -A staticfiles)" ]; then
    echo "Collecting static files..."
    python manage.py collectstatic --noinput
else
    echo "Static files already collected"
fi

echo "Initialization complete."

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

# Trap signals to ensure backup process is cleaned up
trap "kill $BACKUP_PID 2>/dev/null" EXIT

# Start the application with gunicorn
exec gunicorn --bind :$PORT \
    --workers 2 \
    --threads 8 \
    --timeout 0 \
    --access-logfile - \
    --error-logfile - \
    portfolio.wsgi:application