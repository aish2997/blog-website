#!/bin/bash
# Manual deployment script for Cloud Run

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Cloud Run deployment...${NC}"

# Check if required environment variables are set
if [ -z "$GCP_PROJECT_ID" ]; then
    echo -e "${RED}Error: GCP_PROJECT_ID environment variable is not set${NC}"
    echo "Please set it with: export GCP_PROJECT_ID=your-project-id"
    exit 1
fi

if [ -z "$GCP_REGION" ]; then
    echo -e "${YELLOW}GCP_REGION not set, defaulting to us-central1${NC}"
    GCP_REGION="us-central1"
fi

SERVICE_NAME="portfolio-production"
IMAGE_NAME="${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/portfolio-images/portfolio"

# Check if user is authenticated
echo -e "${GREEN}Checking GCloud authentication...${NC}"
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo -e "${RED}Not authenticated. Please run: gcloud auth login${NC}"
    exit 1
fi

# Set the project
echo -e "${GREEN}Setting GCP project to ${GCP_PROJECT_ID}...${NC}"
gcloud config set project ${GCP_PROJECT_ID}

# Configure Docker for Artifact Registry
echo -e "${GREEN}Configuring Docker for Artifact Registry...${NC}"
gcloud auth configure-docker ${GCP_REGION}-docker.pkg.dev

# Build the Docker image
echo -e "${GREEN}Building Docker image...${NC}"
docker build -f docker/Dockerfile -t ${IMAGE_NAME}:latest .

# Push the image
echo -e "${GREEN}Pushing Docker image to Artifact Registry...${NC}"
docker push ${IMAGE_NAME}:latest

# Deploy to Cloud Run
echo -e "${GREEN}Deploying to Cloud Run...${NC}"
gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_NAME}:latest \
    --region ${GCP_REGION} \
    --platform managed \
    --allow-unauthenticated \
    --memory 512Mi \
    --cpu 1 \
    --max-instances 10 \
    --min-instances 0 \
    --port 8080 \
    --set-env-vars "DJANGO_SETTINGS_MODULE=portfolio.settings_production" \
    --set-env-vars "DATABASE_PATH=/tmp/db.sqlite3" \
    --set-env-vars "DEBUG=False" \
    --set-env-vars "ALLOWED_HOSTS=*"

# Get the service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region=${GCP_REGION} --format="value(status.url)")

echo -e "${GREEN}✅ Deployment complete!${NC}"
echo -e "${GREEN}Service URL: ${SERVICE_URL}${NC}"
echo -e "${GREEN}Admin URL: ${SERVICE_URL}/admin${NC}"

# Test the deployment
echo -e "${GREEN}Testing deployment...${NC}"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" ${SERVICE_URL}/health/ || echo "500")
if [ "$HTTP_CODE" == "200" ]; then
    echo -e "${GREEN}✅ Health check passed${NC}"
else
    echo -e "${YELLOW}⚠️ Health check returned HTTP ${HTTP_CODE}${NC}"
fi

echo -e "${GREEN}Done! If the admin panel CSS is not loading, check the Cloud Run logs:${NC}"
echo "gcloud logs read --service=${SERVICE_NAME} --region=${GCP_REGION}"