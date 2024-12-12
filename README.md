# Blog Website

A blog platform built with Next.js (Frontend), FastAPI (Backend), and GCP (Infrastructure).

## Development Setup

### 1. Setting up the Github Actions Service Account in Cloud Console

You can create the service account and assign the specified roles using the `gcloud` CLI. Here's how to do it step-by-step:

### Step 1: Create the Service Account
```bash
gcloud iam service-accounts create github-actions-sa \
  --description="GitHub Actions Service Account" \
  --display-name="GitHub Actions SA" \
  --project=YOUR_PROJECT_NAME
```

### Step 2: Assign Roles to the Service Account
```bash
# DNS Administrator
gcloud projects add-iam-policy-binding YOUR_PROJECT_NAME \
  --member="serviceAccount:github-actions-sa@YOUR_PROJECT_NAME.iam.gserviceaccount.com" \
  --role="roles/dns.admin"

# Service Account Token Creator
gcloud projects add-iam-policy-binding YOUR_PROJECT_NAME \
  --member="serviceAccount:github-actions-sa@YOUR_PROJECT_NAME.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountTokenCreator"

# Storage Admin
gcloud projects add-iam-policy-binding YOUR_PROJECT_NAME \
  --member="serviceAccount:github-actions-sa@YOUR_PROJECT_NAME.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

# Workload Identity User
gcloud iam service-accounts add-iam-policy-binding github-actions-sa@YOUR_PROJECT_NAME.iam.gserviceaccount.com \
  --member="principalSet://iam.googleapis.com/projects/YOUR_PROJECT_NUMBER/locations/global/workloadIdentityPools/YOUR_POOL_NAME/attribute.repository/YOUR_GITHUB_REPO" \
  --role="roles/iam.workloadIdentityUser"
```

### Replace Placeholders
- Replace `YOUR_PROJECT_NUMBER` with your GCP project number (find it using `gcloud projects list`).
- Replace `YOUR_POOL_NAME` with your workload identity pool name.
- Replace `YOUR_GITHUB_REPO` with the GitHub repository in the format `owner/repo` (e.g., `username/repository`).

### Verify the Configuration
After assigning the roles, verify that the service account has the required permissions:
```bash
gcloud projects get-iam-policy YOUR_PROJECT_NAME \
  --flatten="bindings[].members" \
  --filter="bindings.members:github-actions-sa@YOUR_PROJECT_NAME.iam.gserviceaccount.com" \
  --format="table(bindings.role)"
```

This will list all the roles assigned to the service account.

1. Add instructions to set up WIF using Gcloud Commands
2. Add instaructions to create state bucket in GCS using Gcloud Commands.
3. Add instructions to add github actions service account as well.

To access the webapp use the below URL.
 
 ```
 http://[YOUR_BUCKET_NAME].storage.googleapis.com
 ```