#!/bin/bash

# Deployment script for Google Cloud Run

set -e

# Configuration
PROJECT_ID=${GCP_PROJECT_ID:-"your-project-id"}
REGION=${REGION:-"us-central1"}
SERVICE_NAME="portfolio"
CLOUD_SQL_INSTANCE="portfolio-db"
BUCKET_NAME="${PROJECT_ID}-portfolio-media"

echo "🚀 Starting deployment to Google Cloud Run..."

# 1. Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI is not installed. Please install it first."
    exit 1
fi

# 2. Set the project
echo "📦 Setting project to ${PROJECT_ID}..."
gcloud config set project ${PROJECT_ID}

# 3. Enable required APIs
echo "🔧 Enabling required APIs..."
gcloud services enable \
    run.googleapis.com \
    sqladmin.googleapis.com \
    secretmanager.googleapis.com \
    cloudbuild.googleapis.com \
    storage.googleapis.com \
    compute.googleapis.com

# 4. Create Cloud Storage bucket for media files
echo "🗂️ Creating Cloud Storage bucket..."
gsutil mb -p ${PROJECT_ID} -l ${REGION} gs://${BUCKET_NAME} || echo "Bucket already exists"
gsutil iam ch allUsers:objectViewer gs://${BUCKET_NAME}

# 5. Create Cloud SQL instance (if not exists)
echo "🗄️ Setting up Cloud SQL..."
gcloud sql instances describe ${CLOUD_SQL_INSTANCE} &> /dev/null || \
gcloud sql instances create ${CLOUD_SQL_INSTANCE} \
    --database-version=POSTGRES_14 \
    --tier=db-f1-micro \
    --region=${REGION} \
    --network=default

# 6. Create database
echo "📊 Creating database..."
gcloud sql databases create portfolio --instance=${CLOUD_SQL_INSTANCE} || echo "Database already exists"

# 7. Create database user
echo "👤 Creating database user..."
gcloud sql users create django --instance=${CLOUD_SQL_INSTANCE} --password=changeme || echo "User already exists"

# 8. Create secrets in Secret Manager
echo "🔐 Creating secrets..."

# Django Secret Key
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())' | \
gcloud secrets create DJANGO_SECRET_KEY --data-file=- || echo "Secret already exists"

# Database password
echo "changeme" | gcloud secrets create DB_PASSWORD --data-file=- || echo "Secret already exists"

# SendGrid API Key (you'll need to update this with your actual key)
echo "your-sendgrid-api-key" | gcloud secrets create SENDGRID_API_KEY --data-file=- || echo "Secret already exists"

# 9. Grant Cloud Run service account access to secrets
PROJECT_NUMBER=$(gcloud projects describe ${PROJECT_ID} --format="value(projectNumber)")
SERVICE_ACCOUNT="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

echo "🔑 Granting secret access..."
for secret in DJANGO_SECRET_KEY DB_PASSWORD SENDGRID_API_KEY; do
    gcloud secrets add-iam-policy-binding ${secret} \
        --member="serviceAccount:${SERVICE_ACCOUNT}" \
        --role="roles/secretmanager.secretAccessor" || true
done

# 10. Build and deploy using Cloud Build
echo "🏗️ Building and deploying to Cloud Run..."
gcloud builds submit \
    --config cloudbuild.yaml \
    --substitutions=_REGION=${REGION},_CLOUD_SQL_CONNECTION_NAME=${PROJECT_ID}:${REGION}:${CLOUD_SQL_INSTANCE},_DB_NAME=portfolio,_DB_USER=django,_GCS_BUCKET_NAME=${BUCKET_NAME}

# 11. Run migrations
echo "🔄 Running database migrations..."
gcloud run jobs create migrate-db \
    --image gcr.io/${PROJECT_ID}/portfolio:latest \
    --region ${REGION} \
    --add-cloudsql-instances ${PROJECT_ID}:${REGION}:${CLOUD_SQL_INSTANCE} \
    --set-env-vars CLOUD_SQL_CONNECTION_NAME=${PROJECT_ID}:${REGION}:${CLOUD_SQL_INSTANCE},DB_NAME=portfolio,DB_USER=django,GCS_BUCKET_NAME=${BUCKET_NAME},DJANGO_SETTINGS_MODULE=portfolio.settings_production \
    --set-secrets DB_PASSWORD=DB_PASSWORD:latest,DJANGO_SECRET_KEY=DJANGO_SECRET_KEY:latest \
    --command "python,manage.py,migrate" || true

gcloud run jobs execute migrate-db --region ${REGION}

# 12. Create superuser (interactive)
echo "👤 Creating superuser..."
read -p "Do you want to create a superuser now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    gcloud run jobs create createsuperuser \
        --image gcr.io/${PROJECT_ID}/portfolio:latest \
        --region ${REGION} \
        --add-cloudsql-instances ${PROJECT_ID}:${REGION}:${CLOUD_SQL_INSTANCE} \
        --set-env-vars CLOUD_SQL_CONNECTION_NAME=${PROJECT_ID}:${REGION}:${CLOUD_SQL_INSTANCE},DB_NAME=portfolio,DB_USER=django,GCS_BUCKET_NAME=${BUCKET_NAME},DJANGO_SETTINGS_MODULE=portfolio.settings_production \
        --set-secrets DB_PASSWORD=DB_PASSWORD:latest,DJANGO_SECRET_KEY=DJANGO_SECRET_KEY:latest \
        --command "python,manage.py,createsuperuser" || true

    gcloud run jobs execute createsuperuser --region ${REGION}
fi

# 13. Get the service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format="value(status.url)")

echo "✅ Deployment complete!"
echo "🌐 Your portfolio is live at: ${SERVICE_URL}"
echo "🔧 Admin panel: ${SERVICE_URL}/admin/"
echo ""
echo "📝 Next steps:"
echo "1. Update the DB_PASSWORD secret with a secure password"
echo "2. Update the SENDGRID_API_KEY secret with your actual API key"
echo "3. Configure your custom domain (optional)"
echo "4. Set up Cloud CDN for better performance (optional)"