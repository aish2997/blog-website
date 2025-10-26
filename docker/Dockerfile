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
    DATABASE_PATH=/app/data/db.sqlite3

# No runtime dependencies needed for SQLite (it's built-in)

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Set work directory
WORKDIR /app

# Copy only the application code
COPY app/ .

# Create a non-root user to run the app
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/data && \
    mkdir -p /app/staticfiles && \
    chown -R appuser:appuser /app

USER appuser

# Run migrations to initialize the SQLite database
RUN python manage.py migrate --noinput || true

# Collect static files (will be uploaded to GCS in production)
RUN python manage.py collectstatic --noinput || true

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health/', timeout=2)" || exit 1

# Run the application
CMD exec gunicorn --bind :$PORT --workers 2 --threads 8 --timeout 0 --access-logfile - --error-logfile - portfolio.wsgi:application