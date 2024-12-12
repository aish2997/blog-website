# Blog Website

A blog platform built with Next.js (Frontend), FastAPI (Backend), and GCP (Infrastructure).

## 1. Setting up Workload Indetity Pool and Provider

Here is the `gcloud` command to create and configure a Workload Identity Pool and a provider with the specified settings:

### Step 1: Create the Workload Identity Pool
```bash
gcloud iam workload-identity-pools create github-actions-pool \
  --project="YOUR_PROJECT_ID" \
  --location="global" \
  --display-name="GitHub Actions Pool"
```

### Step 2: Create the Workload Identity Pool Provider
```bash
gcloud iam workload-identity-pools providers create-oidc github-actions-provider \
  --workload-identity-pool="github-actions-pool" \
  --project="YOUR_PROJECT_ID" \
  --location="global" \
  --display-name="GitHub Actions Provider" \
  --issuer-uri="https://token.actions.githubusercontent.com" \
  --attribute-mapping="attribute.aud=assertion.aud,attribute.actor=assertion.actor,attribute.repository=assertion.repository,google.subject=assertion.sub" \
  --attribute-condition="attribute.repository=='aish2997/blog-website'"
```

### Explanation of Commands
1. **Create the Workload Identity Pool:**
   - `github-actions-pool` is the name of the pool.
   - Replace `YOUR_PROJECT_ID` with your actual GCP project ID.

2. **Create the OIDC Provider:**
   - `github-actions-provider` is the name of the provider.
   - The `issuer-uri` is set to `https://token.actions.githubusercontent.com` for GitHub Actions.
   - `--attribute-mapping` defines the mapping of OIDC attributes to Google attributes:
     - `attribute.aud = assertion.aud`
     - `attribute.actor = assertion.actor`
     - `attribute.repository = assertion.repository`
     - `google.subject = assertion.sub`
   - `--attribute-condition` restricts authentication to GitHub repositories matching the condition `attribute.repository=='aish2997/blog-website'`.

3. **Default Audience:**
   - By default, the audience (`aud`) of the OIDC token must match the full canonical resource name of the Workload Identity Pool Provider unless explicitly specified otherwise. You do not need to set an additional audience in this configuration.

### Verification
After completing these steps, verify the configuration:
```bash
gcloud iam workload-identity-pools describe github-actions-pool \
  --project="YOUR_PROJECT_ID" \
  --location="global"

gcloud iam workload-identity-pools providers describe github-actions-provider \
  --workload-identity-pool="github-actions-pool" \
  --project="YOUR_PROJECT_ID" \
  --location="global"
```

These commands will output the details of the pool and provider to confirm everything is set up correctly.

## 2. Setting up the Github Actions Service Account

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

## 3. Setting up the state file bucket in GCS

Here are the `gcloud` commands to create a GCS bucket with the specified directory structure:

### Step 1: Create the GCS Bucket
```bash
gcloud storage buckets create gs://YOUR_PROJECT_ID-state \
  --project="YOUR_PROJECT_ID" \
  --location="eu" \
  --default-storage-class="STANDARD" \
  --uniform-bucket-level-access
```

1. Add instructions to set up WIF using Gcloud Commands
2. Add instaructions to create state bucket in GCS using Gcloud Commands.
3. Add instructions to add github actions service account as well.
4. IAM Service Account Credentials API Enable this API

To access the webapp use the below URL.
 
 ```
 http://[YOUR_BUCKET_NAME].storage.googleapis.com
 ```