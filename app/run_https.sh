#!/bin/bash

# Run Django development server with HTTPS
# This script starts the server on https://localhost:8000

# Load environment variables from .env
export $(cat /Users/aishwaryabhargava/blog-website/app/.env | grep -v '^#' | xargs)

echo "🔒 Starting Django development server with HTTPS..."
echo ""
echo "Server will be available at:"
echo "  👉 https://localhost:8000/"
echo "  👉 https://127.0.0.1:8000/"
echo ""
echo "Note: Your browser will show a security warning because this is a"
echo "self-signed certificate. Click 'Advanced' → 'Proceed to localhost'"
echo ""

# Run the server with auto-generated SSL certificate using venv Python
/Users/aishwaryabhargava/blog-website/venv/bin/python manage.py runserver_plus --cert-file /tmp/cert 0.0.0.0:8000
