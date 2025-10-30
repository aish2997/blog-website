#!/bin/bash

# Script to add Neon DATABASE_URL to Google Secret Manager
# This should be run after Terraform creates the secret container

set -e

# Neon PRODUCTION branch database URL (NOT dev branch!)
DATABASE_URL="postgresql://neondb_owner:npg_aE1htmuSIPA4@ep-falling-fire-agw51vny-pooler.c-2.eu-central-1.aws.neon.tech/neondb?sslmode=require"

# Secret name (must match what's in Terraform)
SECRET_NAME="neon-database-url"

echo "Adding Neon DATABASE_URL to Google Secret Manager..."
echo "Secret name: $SECRET_NAME"

# Add the secret value
echo -n "$DATABASE_URL" | gcloud secrets versions add "$SECRET_NAME" --data-file=-

echo "✅ Secret added successfully!"
echo ""
echo "Next steps:"
echo "1. Run Terraform to create the Cloud Run service with the new configuration"
echo "2. Deploy your application"
echo "3. Verify the application connects to Neon PostgreSQL"
