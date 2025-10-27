# Django Portfolio on Cloud Run - Manual Setup Guide

This guide provides step-by-step instructions for setting up Django admin credentials and managing your portfolio application on Google Cloud Run with zero-cost SQLite persistence.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Initial Setup](#initial-setup)
3. [Admin Portal Configuration](#admin-portal-configuration)
4. [Database Persistence](#database-persistence)
5. [Troubleshooting](#troubleshooting)
6. [Maintenance](#maintenance)

---

## Prerequisites

Ensure you have the following installed and configured:
- Google Cloud CLI (`gcloud`)
- Terraform (>= 1.0)
- Docker
- GitHub repository with secrets configured

## Initial Setup

### 1. Run Bootstrap (One-time setup)

If not already done, run the bootstrap to create base infrastructure:

```bash
cd terraform/bootstrap
terraform init
terraform apply
```

This creates:
- Service accounts
- Artifact Registry
- Secret Manager secrets
- State bucket for Terraform

### 2. Configure GitHub Secrets

After bootstrap, configure these secrets in your GitHub repository:

```bash
# Get the values from Terraform output
cd terraform/bootstrap
terraform output

# Add to GitHub Secrets:
# - WIF_PROVIDER
# - WIF_SERVICE_ACCOUNT
# - TF_STATE_BUCKET
# - GCP_PROJECT_ID
# - GCP_REGION
```

## Admin Portal Configuration

### Method 1: Using Secret Manager (Recommended)

This is the most secure method and credentials persist across deployments.

#### Step 1: Create/Update Superuser Secrets

```bash
# Set your project ID
export PROJECT_ID="your-project-id"

# Create or update the secrets
echo -n "admin" | gcloud secrets create django-superuser-username --data-file=- --project=$PROJECT_ID 2>/dev/null || \
echo -n "admin" | gcloud secrets versions add django-superuser-username --data-file=- --project=$PROJECT_ID

echo -n "admin@yourdomain.com" | gcloud secrets create django-superuser-email --data-file=- --project=$PROJECT_ID 2>/dev/null || \
echo -n "admin@yourdomain.com" | gcloud secrets versions add django-superuser-email --data-file=- --project=$PROJECT_ID

echo -n "YourSecurePassword123!" | gcloud secrets create django-superuser-password --data-file=- --project=$PROJECT_ID 2>/dev/null || \
echo -n "YourSecurePassword123!" | gcloud secrets versions add django-superuser-password --data-file=- --project=$PROJECT_ID
```

#### Step 2: Grant Access to Cloud Run Service Account

```bash
# Grant the Cloud Run service account access to read the secrets
gcloud secrets add-iam-policy-binding django-superuser-username \
    --member="serviceAccount:portfolio-cloud-run-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor" \
    --project=$PROJECT_ID

gcloud secrets add-iam-policy-binding django-superuser-email \
    --member="serviceAccount:portfolio-cloud-run-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor" \
    --project=$PROJECT_ID

gcloud secrets add-iam-policy-binding django-superuser-password \
    --member="serviceAccount:portfolio-cloud-run-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor" \
    --project=$PROJECT_ID
```

#### Step 3: Redeploy Cloud Run Service

```bash
# Option A: Via GitHub Actions (Recommended)
# Push to main branch or trigger the deploy workflow manually

# Option B: Via Terraform
cd terraform/infrastructure
terraform apply

# Option C: Via gcloud (Quick update)
gcloud run services update portfolio-production \
    --update-env-vars="DJANGO_SUPERUSER_USERNAME=projects/$PROJECT_ID/secrets/django-superuser-username:latest" \
    --update-env-vars="DJANGO_SUPERUSER_EMAIL=projects/$PROJECT_ID/secrets/django-superuser-email:latest" \
    --update-env-vars="DJANGO_SUPERUSER_PASSWORD=projects/$PROJECT_ID/secrets/django-superuser-password:latest" \
    --region=us-central1 \
    --project=$PROJECT_ID
```

### Method 2: Using Terraform Variables

You can also set superuser credentials via Terraform:

```bash
cd terraform/infrastructure

# Create terraform.tfvars file
cat > terraform.tfvars <<EOF
django_superuser_username = "admin"
django_superuser_email    = "admin@yourdomain.com"
django_superuser_password = "YourSecurePassword123!"
EOF

# Apply with variables
terraform apply
```

### Method 3: One-Time Cloud Run Job

For a quick one-time setup without Secret Manager:

```bash
# Create and run a one-time job
gcloud run jobs create create-superuser \
    --image=gcr.io/$PROJECT_ID/portfolio:latest \
    --region=us-central1 \
    --command="python,manage.py,createsuperuser,--noinput" \
    --set-env-vars="DJANGO_SUPERUSER_USERNAME=admin" \
    --set-env-vars="DJANGO_SUPERUSER_EMAIL=admin@yourdomain.com" \
    --set-env-vars="DJANGO_SUPERUSER_PASSWORD=YourSecurePassword123!" \
    --set-env-vars="GCS_BUCKET_MEDIA=$PROJECT_ID-portfolio-media-production" \
    --project=$PROJECT_ID

# Execute the job
gcloud run jobs execute create-superuser --region=us-central1 --project=$PROJECT_ID

# Check job logs
gcloud run jobs executions list --job=create-superuser --region=us-central1 --project=$PROJECT_ID
```

## Database Persistence

Your SQLite database is automatically persisted using Google Cloud Storage with zero additional cost:

### How It Works

1. **On Container Start**: Database is downloaded from GCS (if exists)
2. **Every 30 Minutes**: Automatic backup to GCS
3. **Timestamped Backups**: Last 5 backups are retained
4. **On Container Stop**: Final backup (handled gracefully)

### Manual Database Management

#### Backup Database Manually

```bash
# SSH into the running container
gcloud run services exec portfolio-production --region=us-central1 --project=$PROJECT_ID -- \
    python manage.py sync_database --action backup --force
```

#### Restore Database

```bash
# The database is automatically restored on container start
# To force restore:
gcloud run services exec portfolio-production --region=us-central1 --project=$PROJECT_ID -- \
    python manage.py sync_database --action restore
```

#### Download Database Locally

```bash
# Download from GCS for local inspection
gsutil cp gs://$PROJECT_ID-portfolio-media-production/database-backups/portfolio.sqlite3 ./local_db.sqlite3

# View with SQLite
sqlite3 local_db.sqlite3
```

#### Upload Modified Database

```bash
# Upload a modified database (use with caution!)
gsutil cp ./local_db.sqlite3 gs://$PROJECT_ID-portfolio-media-production/database-backups/portfolio.sqlite3
```

## Troubleshooting

### Admin CSS/JS Not Loading

If admin portal appears without styling:

1. **Check Static Files Collection**:
```bash
# View container logs
gcloud run services logs read portfolio-production --region=us-central1 --project=$PROJECT_ID --limit=50

# Look for "Admin static files collected successfully"
```

2. **Force Rebuild and Deploy**:
```bash
# Rebuild with --no-cache to ensure static files are collected
docker build --no-cache -t gcr.io/$PROJECT_ID/portfolio:latest -f docker/Dockerfile .
docker push gcr.io/$PROJECT_ID/portfolio:latest

# Deploy
gcloud run deploy portfolio-production \
    --image=gcr.io/$PROJECT_ID/portfolio:latest \
    --region=us-central1 \
    --project=$PROJECT_ID
```

3. **Use GCS for Static Files** (Recommended for production):
```bash
# The infrastructure already creates static bucket
# Just redeploy - it will automatically use GCS
cd terraform/infrastructure
terraform apply
```

### Cannot Login to Admin

1. **Verify Secrets are Set**:
```bash
# Check if secrets exist
gcloud secrets list --project=$PROJECT_ID | grep django-superuser

# View secret versions (not the actual value)
gcloud secrets versions list django-superuser-username --project=$PROJECT_ID
```

2. **Check Container Logs**:
```bash
# Look for "Superuser created successfully" or errors
gcloud run services logs read portfolio-production --region=us-central1 --project=$PROJECT_ID | grep -i superuser
```

3. **Verify Environment Variables**:
```bash
# Check service configuration
gcloud run services describe portfolio-production --region=us-central1 --project=$PROJECT_ID --format="value(spec.template.spec.containers[0].env[].name)"
```

### Database Issues

1. **Database Not Persisting**:
```bash
# Check GCS bucket permissions
gsutil iam get gs://$PROJECT_ID-portfolio-media-production

# Verify backup is happening
gcloud run services logs read portfolio-production --region=us-central1 --project=$PROJECT_ID | grep "database backup"
```

2. **Database Corrupted**:
```bash
# Restore from a timestamped backup
gsutil ls gs://$PROJECT_ID-portfolio-media-production/database-backups/archive/

# Copy a specific backup
gsutil cp gs://$PROJECT_ID-portfolio-media-production/database-backups/archive/portfolio_20240315_120000.sqlite3 \
          gs://$PROJECT_ID-portfolio-media-production/database-backups/portfolio.sqlite3
```

## Maintenance

### Regular Tasks

#### 1. Update Superuser Password

```bash
# Update in Secret Manager
echo -n "NewSecurePassword456!" | gcloud secrets versions add django-superuser-password --data-file=- --project=$PROJECT_ID

# Restart service to pick up new password
gcloud run services update portfolio-production --region=us-central1 --project=$PROJECT_ID --no-traffic
```

#### 2. Monitor Database Size

```bash
# Check database size in GCS
gsutil du -sh gs://$PROJECT_ID-portfolio-media-production/database-backups/
```

#### 3. Clean Up Old Backups

```bash
# List all backups
gsutil ls -l gs://$PROJECT_ID-portfolio-media-production/database-backups/archive/

# The sync_database command automatically keeps only last 5 backups
# Manual cleanup if needed:
gsutil rm gs://$PROJECT_ID-portfolio-media-production/database-backups/archive/portfolio_OLD_TIMESTAMP.sqlite3
```

#### 4. View Application Metrics

```bash
# View Cloud Run metrics
gcloud run services describe portfolio-production \
    --region=us-central1 \
    --project=$PROJECT_ID \
    --format="table(status.traffic[].percent,status.traffic[].latestRevision,status.traffic[].revisionName)"

# View logs
gcloud run services logs read portfolio-production \
    --region=us-central1 \
    --project=$PROJECT_ID \
    --limit=100
```

### Security Best Practices

1. **Rotate Secrets Regularly**:
   - Update passwords every 90 days
   - Use strong, unique passwords
   - Never commit credentials to git

2. **Monitor Access**:
```bash
# View secret access logs
gcloud logging read "resource.type=secretmanager.googleapis.com/Secret" \
    --project=$PROJECT_ID \
    --limit=20
```

3. **Restrict Admin Access**:
   - Consider using Cloud IAP for additional security
   - Limit ALLOWED_HOSTS in production
   - Use HTTPS only

4. **Backup Strategy**:
   - Download monthly backups to separate storage
   - Test restore procedures regularly
   - Document your data recovery process

## Quick Reference

### Common Commands

```bash
# View service URL
gcloud run services describe portfolio-production --region=us-central1 --project=$PROJECT_ID --format="value(status.url)"

# Restart service (picks up new secrets)
gcloud run services update portfolio-production --region=us-central1 --project=$PROJECT_ID --no-traffic

# View recent logs
gcloud run services logs read portfolio-production --region=us-central1 --project=$PROJECT_ID --limit=50

# SSH into container
gcloud run services exec portfolio-production --region=us-central1 --project=$PROJECT_ID -- /bin/bash

# Run Django management command
gcloud run services exec portfolio-production --region=us-central1 --project=$PROJECT_ID -- python manage.py [command]
```

### Environment Variables

Key environment variables used by the application:

- `DJANGO_SUPERUSER_USERNAME`: Admin username (from Secret Manager)
- `DJANGO_SUPERUSER_EMAIL`: Admin email (from Secret Manager)
- `DJANGO_SUPERUSER_PASSWORD`: Admin password (from Secret Manager)
- `GCS_BUCKET_MEDIA`: Media files bucket
- `GCS_BUCKET_STATIC`: Static files bucket
- `DATABASE_PATH`: `/tmp/db.sqlite3` (SQLite location)
- `K_SERVICE`: Set by Cloud Run (used to detect Cloud Run environment)

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review Cloud Run logs for errors
3. Ensure all prerequisites are met
4. Verify GCP permissions and quotas

Remember: The SQLite database with GCS backup provides a zero-cost persistence solution perfect for portfolio sites with moderate traffic!