#!/bin/bash
# Simple entrypoint script without GCS sync for debugging

echo "Starting Django application (simple mode)..."

# Database path
DATABASE_PATH=${DATABASE_PATH:-/tmp/db.sqlite3}
echo "Database path: $DATABASE_PATH"

# Run migrations to create/update database
echo "Running database migrations..."
python manage.py migrate --noinput || {
    echo "Warning: Migrations failed, but continuing..."
}

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput || {
    echo "Warning: Static files collection failed, but continuing..."
}

echo "Starting Gunicorn..."

# Start the application with gunicorn (1 worker for SQLite)
exec gunicorn --bind :$PORT \
    --workers 1 \
    --threads 4 \
    --timeout 0 \
    --access-logfile - \
    --error-logfile - \
    portfolio.wsgi:application