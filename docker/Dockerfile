# Multi-stage build for optimized production image
FROM python:3.9-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
WORKDIR /app
COPY app/requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install gunicorn google-cloud-secret-manager

# Production image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080 \
    DJANGO_SETTINGS_MODULE=portfolio.settings_production \
    DATABASE_PATH=/tmp/db.sqlite3

# No runtime dependencies needed for SQLite (it's built-in)

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Set work directory
WORKDIR /app

# Copy only the application code
COPY app/ .

# Copy entrypoint script
COPY docker/entrypoint.sh /app/entrypoint.sh

# Collect static files during build (including admin assets)
# This ensures all static files are bundled in the image
RUN DJANGO_SETTINGS_MODULE=portfolio.settings python manage.py collectstatic --noinput || echo "Static collection during build skipped"

# Create a non-root user to run the app
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/staticfiles /tmp/staticfiles && \
    chmod +x /app/entrypoint.sh && \
    chown -R appuser:appuser /app && \
    # Ensure /tmp/staticfiles is writable by appuser
    chown -R appuser:appuser /tmp/staticfiles || true

USER appuser

# Note: Database initialization and migrations are now handled by entrypoint.sh at runtime
# This ensures the database is created in /tmp which is writable in Cloud Run

# Run the application using the entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]