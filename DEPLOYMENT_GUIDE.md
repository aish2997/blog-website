# Deployment Guide - Portfolio Django App to Google Cloud Run

This guide walks you through deploying the portfolio Django application to Google Cloud Run using GitHub Actions with Workload Identity Federation (WIF).

## Architecture Overview

The deployment uses a fully automated CI/CD pipeline with the following components:

- **GitHub Actions**: Orchestrates the deployment pipeline
- **Workload Identity Federation**: Secure, keyless authentication to GCP
- **Terraform**: Infrastructure as Code for all GCP resources
- **Cloud Run**: Serverless platform for running the Django application
- **Cloud SQL**: Managed PostgreSQL database
- **Cloud Storage**: Object storage for static and media files
- **Artifact Registry**: Docker container registry
- **Secret Manager**: Secure storage for sensitive configuration

## Prerequisites

1. **Google Cloud Project** with billing enabled
2. **gcloud CLI** installed locally
3. **GitHub Repository** with the code
4. **Initial GCP Service Account** with Owner or Editor role (only for bootstrap)

## Initial Setup

### Step 1: Prepare GCP Project

```bash
# Set your project ID
export PROJECT_ID="your-project-id"
gcloud config set project $PROJECT_ID

# Create initial service account for bootstrap
gcloud iam service-accounts create initial-setup \
  --display-name="Initial Setup Account"

# Grant necessary permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:initial-setup@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/owner"

# Create and download key
gcloud iam service-accounts keys create ~/initial-setup-key.json \
  --iam-account=initial-setup@$PROJECT_ID.iam.gserviceaccount.com
```

### Step 2: Configure GitHub Repository

1. **Add the initial service account key as a secret**:
   - Go to Settings → Secrets and variables → Actions
   - Create a new secret named `GCP_SA_KEY`
   - Paste the contents of `~/initial-setup-key.json`

2. **Run the Bootstrap Workflow**:
   - Go to Actions → Bootstrap Infrastructure
   - Click "Run workflow"
   - Fill in the required inputs:
     - GCP Project ID: Your project ID
     - GCP Region: us-central1 (or your preferred region)
     - GitHub Owner: Your GitHub username or organization
     - GitHub Repository: Your repository name
   - Click "Run workflow"

3. **Save Bootstrap Outputs**:
   After the workflow completes, it will display important outputs. Save these values.

### Step 3: Configure Repository Secrets for WIF

After bootstrap completes, add the following secrets to your repository:

| Secret Name | Value | Description |
|------------|-------|-------------|
| `WIF_PROVIDER` | From bootstrap output | Workload Identity Provider |
| `WIF_SERVICE_ACCOUNT` | From bootstrap output | Service Account for GitHub Actions |
| `GCP_PROJECT_ID` | Your project ID | Google Cloud Project ID |
| `GCP_REGION` | us-central1 | Deployment region |
| `TF_STATE_BUCKET` | From bootstrap output | Terraform state bucket |

### Step 4: Clean Up Initial Service Account

After setting up WIF, delete the initial service account key for security:

```bash
# Delete the key file
rm ~/initial-setup-key.json

# Remove the GCP_SA_KEY secret from GitHub
# (Do this via GitHub UI)

# Optionally, delete the service account
gcloud iam service-accounts delete initial-setup@$PROJECT_ID.iam.gserviceaccount.com
```

## Regular Deployment

Once the initial setup is complete, deployments are fully automated:

### Automatic Deployment

Pushing to the `main` or `production` branch triggers automatic deployment:

```bash
git add .
git commit -m "Your changes"
git push origin main
```

### Manual Deployment

You can also trigger deployment manually:

1. Go to Actions → Deploy to Cloud Run
2. Click "Run workflow"
3. Select the environment (production/staging)
4. Click "Run workflow"

## Deployment Pipeline

The deployment workflow performs these steps:

1. **Infrastructure Phase**:
   - Provisions/updates Cloud SQL instance
   - Creates/updates Cloud Storage buckets
   - Configures VPC and networking
   - Sets up Cloud Run service configuration

2. **Build Phase**:
   - Builds Docker image with multi-stage build
   - Pushes image to Artifact Registry
   - Tags with both `latest` and commit SHA

3. **Deploy Phase**:
   - Updates Cloud Run with new image
   - Runs database migrations
   - Performs health checks

4. **Smoke Tests**:
   - Verifies application is accessible
   - Tests critical endpoints

## Environment Variables

The application uses the following environment variables in production:

| Variable | Description | Set By |
|----------|-------------|--------|
| `DJANGO_SETTINGS_MODULE` | `portfolio.settings_production` | Terraform |
| `GCP_PROJECT_ID` | Project ID | Terraform |
| `DATABASE_URL` | PostgreSQL connection string | Terraform |
| `CLOUD_SQL_CONNECTION_NAME` | Cloud SQL instance | Terraform |
| `GCS_BUCKET_MEDIA` | Media files bucket | Terraform |
| `GCS_BUCKET_STATIC` | Static files bucket | Terraform |
| `SECRET_KEY` | Django secret key | Secret Manager |
| `DEBUG` | False in production | Terraform |

## Managing Secrets

Secrets are stored in Google Secret Manager:

```bash
# Update Django secret key
echo -n "your-new-secret-key" | gcloud secrets versions add django-secret-key --data-file=-

# Update database password
echo -n "your-new-password" | gcloud secrets versions add db-password --data-file=-
```

## Database Management

### Run Migrations Manually

```bash
# Via Cloud Run Jobs
gcloud run jobs create manual-migrate \
  --image $REGION-docker.pkg.dev/$PROJECT_ID/portfolio-images/portfolio:latest \
  --region $REGION \
  --command python \
  --args "manage.py,migrate"

gcloud run jobs execute manual-migrate --region $REGION --wait
```

### Access Django Shell

```bash
# Create a job for shell access
gcloud run jobs create django-shell \
  --image $REGION-docker.pkg.dev/$PROJECT_ID/portfolio-images/portfolio:latest \
  --region $REGION \
  --command python \
  --args "manage.py,shell"

# Execute interactively (Note: Limited interactivity)
gcloud run jobs execute django-shell --region $REGION --wait
```

### Create Superuser

```bash
# Via Cloud SQL proxy
gcloud sql connect portfolio-db-production --user=portfolio_user --database=portfolio

# Then in your local environment with DATABASE_URL set:
python manage.py createsuperuser
```

## Monitoring

### View Logs

```bash
# Cloud Run logs
gcloud run services logs read portfolio-production --region=$REGION

# Cloud SQL logs
gcloud sql operations list --instance=portfolio-db-production
```

### View Metrics

Access the Google Cloud Console:
- Cloud Run: Monitor CPU, memory, request count
- Cloud SQL: Monitor connections, storage, performance
- Cloud Storage: Monitor bandwidth, operations

## Rollback

### Quick Rollback via Cloud Run

```bash
# List revisions
gcloud run revisions list --service=portfolio-production --region=$REGION

# Route traffic to previous revision
gcloud run services update-traffic portfolio-production \
  --to-revisions=PREVIOUS_REVISION=100 \
  --region=$REGION
```

### Rollback via GitHub

1. Revert the commit:
```bash
git revert HEAD
git push origin main
```

2. Or redeploy a previous commit:
   - Go to Actions → Deploy to Cloud Run
   - Run workflow from a specific branch/tag

## Custom Domain Setup

1. **Verify domain ownership** in Google Search Console

2. **Update Terraform variables**:
   Add your domain in `terraform/infrastructure/terraform.tfvars`:
   ```hcl
   domain = "yourdomain.com"
   ```

3. **Run deployment** to create domain mapping

4. **Update DNS records** with provided values

## Troubleshooting

### Common Issues

**Issue**: Cloud SQL connection fails
- Check VPC connector configuration
- Verify Cloud SQL has private IP
- Check service account permissions

**Issue**: Static files not loading
- Verify GCS bucket permissions (should be public)
- Check STATIC_URL and MEDIA_URL settings
- Run `collectstatic` in deployment

**Issue**: Migrations fail
- Check database connectivity
- Verify migration job has correct Cloud SQL connection
- Check for migration conflicts

**Issue**: WIF authentication fails
- Verify WIF provider configuration
- Check repository and owner names match
- Ensure service account has correct permissions

### Debug Commands

```bash
# Check service status
gcloud run services describe portfolio-production --region=$REGION

# Check recent deployments
gcloud run revisions list --service=portfolio-production --region=$REGION

# Test database connection
gcloud sql connect portfolio-db-production --user=portfolio_user

# Check secret values
gcloud secrets versions list django-secret-key
```

## Security Best Practices

1. **Never commit secrets** to the repository
2. **Use WIF** instead of service account keys
3. **Regularly rotate** secrets in Secret Manager
4. **Enable** Cloud Audit Logs
5. **Use** least privilege for service accounts
6. **Enable** VPC Service Controls for additional security
7. **Regular** security updates for dependencies

## Cost Optimization

1. **Cloud Run**: Set appropriate min/max instances
2. **Cloud SQL**: Use appropriate tier, enable auto-stop for dev
3. **Storage**: Set lifecycle policies for old files
4. **Artifact Registry**: Clean up old images regularly

```bash
# Clean up old images (keep last 10)
gcloud artifacts docker images list \
  --repository=portfolio-images \
  --location=$REGION \
  --format="value(IMAGE)" | \
  tail -n +11 | \
  xargs -I {} gcloud artifacts docker images delete {} --quiet
```

## Support

For issues or questions:
1. Check the [GitHub Issues](https://github.com/your-org/your-repo/issues)
2. Review Cloud Run logs
3. Consult the Django documentation
4. Check Google Cloud documentation