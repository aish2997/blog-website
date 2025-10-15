  1. Improved Project Structure

  blog-website/
  ├── app/                    # Django application (isolated)
  │   ├── apps/              # Django apps
  │   ├── portfolio/         # Project settings
  │   ├── templates/         # HTML templates
  │   ├── static/           # Static assets
  │   └── requirements.txt  # Dependencies
  ├── terraform/            # Infrastructure as Code
  │   ├── bootstrap/        # One-time setup (WIF, state bucket, AR)
  │   └── infrastructure/   # App infrastructure (Cloud Run, SQL, Storage)
  ├── docker/              # Docker configuration
  │   └── Dockerfile       # Multi-stage optimized build
  ├── .github/             # GitHub Actions
  │   └── workflows/
  │       ├── bootstrap.yaml    # Initial setup workflow
  │       └── deploy.yaml       # Deployment workflow
  └── docs/               # Documentation

  2. Infrastructure as Code (Terraform)

  Bootstrap Module (One-time setup):

  - ✅ Terraform state bucket
  - ✅ Workload Identity Federation (keyless auth)
  - ✅ Artifact Registry for Docker images
  - ✅ Service accounts with least privilege
  - ✅ Initial secrets in Secret Manager

  Infrastructure Module:

  - ✅ Cloud SQL (PostgreSQL) with private IP
  - ✅ VPC and connector for secure database access
  - ✅ Cloud Storage buckets for static/media files
  - ✅ Cloud Run service configuration
  - ✅ Automated backups and monitoring

  3. CI/CD Pipeline (GitHub Actions)

  Features:

  - Secure Authentication: Uses Workload Identity Federation (no keys!)
  - Automated Deployment: Push to main branch triggers deployment
  - Infrastructure Management: Terraform manages all resources
  - Docker Optimization: Multi-stage builds for smaller images
  - Database Migrations: Automated via Cloud Run Jobs
  - Health Checks: Smoke tests after deployment

  4. Production Configuration

  - Django Settings: app/portfolio/settings_production.py with:
    - Google Secret Manager integration
    - Cloud Storage for static/media
    - Cloud SQL connection handling
    - Security best practices
  - Docker: Optimized Dockerfile with:
    - Multi-stage build
    - Non-root user
    - Health checks
    - Production dependencies only

  5. Key Improvements

  - Clean Separation: Application code in app/, infrastructure in terraform/
  - No Secrets in Code: All secrets in Secret Manager
  - Scalable Architecture: Cloud Run auto-scaling
  - Cost Optimized: Resources scale to zero when idle
  - Security First: Private database, WIF auth, least privilege

  Next Steps to Deploy:

  1. Initial Setup (one-time):
  # Create service account for bootstrap
  gcloud iam service-accounts create initial-setup --display-name="Bootstrap"
  gcloud projects add-iam-policy-binding PROJECT_ID \
    --member="serviceAccount:initial-setup@PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/owner"
  gcloud iam service-accounts keys create ~/key.json \
    --iam-account=initial-setup@PROJECT_ID.iam.gserviceaccount.com

  # Add key to GitHub secret: GCP_SA_KEY
  # Run bootstrap workflow via GitHub Actions UI

  2. Configure Secrets (after bootstrap):
  Add these repository secrets from bootstrap outputs:
  - WIF_PROVIDER
  - WIF_SERVICE_ACCOUNT
  - GCP_PROJECT_ID
  - GCP_REGION
  - TF_STATE_BUCKET

  3. Deploy Application:
  git add .
  git commit -m "Deploy to Cloud Run"
  git push origin main

  The deployment will automatically:
  - Provision infrastructure via Terraform
  - Build and push Docker image
  - Deploy to Cloud Run
  - Run database migrations
  - Perform health checks

  Documentation Created:

  - DEPLOYMENT_GUIDE.md - Step-by-step deployment instructions
  - INFRASTRUCTURE_README.md - Infrastructure overview
  - CLAUDE.md - Updated with new structure
