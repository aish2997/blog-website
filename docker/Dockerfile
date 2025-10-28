# Multi-stage build for optimized production image
FROM python:3.12-slim as builder

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
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080 \
    DJANGO_SETTINGS_MODULE=portfolio.settings_production \
    DATABASE_PATH=/tmp/db.sqlite3

# No runtime dependencies needed for SQLite (it's built-in)

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Set work directory
WORKDIR /app

# Copy only the application code
COPY app/ .

# Copy entrypoint script
COPY docker/entrypoint.sh /app/entrypoint.sh

# Create a non-root user to run the app
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/staticfiles /app/static && \
    chmod +x /app/entrypoint.sh && \
    chown -R appuser:appuser /app

# Switch to appuser for running Django commands
USER appuser

# Collect static files during build (including Django admin static files)
# This ensures admin static files are baked into the image
# Note: We use a build-time-only SECRET_KEY since it's not used for security during collectstatic
ENV SECRET_KEY="build-time-key-only-for-collectstatic-not-for-production"
RUN python manage.py collectstatic --noinput --clear && \
    # Verify that admin static files were collected successfully
    test -d /app/staticfiles/admin && \
    test -f /app/staticfiles/admin/css/base.css && \
    echo "✅ Admin static files verified" || \
    (echo "❌ Admin static files missing!" && exit 1)
# Clear the build-time SECRET_KEY so it's not in the final image
ENV SECRET_KEY=""

# Add a health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health/').read()" || exit 1

# Note: Database initialization and migrations are now handled by entrypoint.sh at runtime
# This ensures the database is created in /tmp which is writable in Cloud Run

# Run the application using the entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]