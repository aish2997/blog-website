Here's the improved version of your README:

---

# Blog Website

A blog platform built with **Next.js** (Frontend), **FastAPI** (Backend), and **GCP** (Infrastructure).

---

## 1. Setting Up Workload Identity Pool and Provider

Below are the `gcloud` commands to create and configure a Workload Identity Pool and Provider with the specified settings.

### Step 1: Export Project ID and Create the Workload Identity Pool

```bash
export PROJECT_ID="YOUR_PROJECT_ID"

gcloud iam workload-identity-pools create github-actions-pool \
  --project="$PROJECT_ID" \
  --location="global" \
  --display-name="GitHub Actions Pool"
```

### Step 2: Create the Workload Identity Pool Provider

```bash
gcloud iam workload-identity-pools providers create-oidc github-actions-provider \
  --workload-identity-pool="github-actions-pool" \
  --project="$PROJECT_ID" \
  --location="global" \
  --display-name="GitHub Actions Provider" \
  --issuer-uri="https://token.actions.githubusercontent.com" \
  --attribute-mapping="attribute.aud=assertion.aud,attribute.actor=assertion.actor,attribute.repository=assertion.repository,google.subject=assertion.sub" \
  --attribute-condition="attribute.repository=='aish2997/blog-website'"
```

### Explanation of Commands

1. **Create the Workload Identity Pool**:
   - `github-actions-pool` is the name of the pool.
   - Replace `YOUR_PROJECT_ID` with your actual GCP project ID.

2. **Create the OIDC Provider**:
   - `github-actions-provider` is the name of the provider.
   - The `issuer-uri` is set to `https://token.actions.githubusercontent.com` for GitHub Actions.
   - `--attribute-mapping` defines the mapping of OIDC attributes to Google attributes:
     - `attribute.aud = assertion.aud`
     - `attribute.actor = assertion.actor`
     - `attribute.repository = assertion.repository`
     - `google.subject = assertion.sub`
   - `--attribute-condition` restricts authentication to the repository `aish2997/blog-website`.

### Verification

After completing these steps, verify the configuration:

```bash
gcloud iam workload-identity-pools describe github-actions-pool \
  --project="$PROJECT_ID" \
  --location="global"

gcloud iam workload-identity-pools providers describe github-actions-provider \
  --workload-identity-pool="github-actions-pool" \
  --project="$PROJECT_ID" \
  --location="global"
```

---

## 2. Setting Up the GitHub Actions Service Account

Follow these steps to create the service account and assign the specified roles.

### Step 1: Export Project Name and Create the Service Account

```bash
export PROJECT_NAME="YOUR_PROJECT_NAME"

gcloud iam service-accounts create github-actions-sa \
  --description="GitHub Actions Service Account" \
  --display-name="GitHub Actions SA" \
  --project="$PROJECT_NAME"
```

### Step 2: Assign Roles to the Service Account

```bash
export SA_EMAIL="github-actions-sa@$PROJECT_NAME.iam.gserviceaccount.com"
export PROJECT_NUMBER=$(gcloud projects describe $PROJECT_NAME --format="value(projectNumber)")
export POOL_NAME="github-actions-pool"
export GITHUB_REPO="aish2997/blog-website"

# DNS Administrator
gcloud projects add-iam-policy-binding "$PROJECT_NAME" \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/dns.admin"

# Service Account Token Creator
gcloud projects add-iam-policy-binding "$PROJECT_NAME" \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/iam.serviceAccountTokenCreator"

# Storage Admin
gcloud projects add-iam-policy-binding "$PROJECT_NAME" \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/storage.admin"

# Workload Identity User
gcloud iam service-accounts add-iam-policy-binding "$SA_EMAIL" \
  --member="principalSet://iam.googleapis.com/projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/$POOL_NAME/attribute.repository/$GITHUB_REPO" \
  --role="roles/iam.workloadIdentityUser"
```

### Verify the Configuration

After assigning the roles, verify the service account permissions:

```bash
gcloud projects get-iam-policy "$PROJECT_NAME" \
  --flatten="bindings[].members" \
  --filter="bindings.members:$SA_EMAIL" \
  --format="table(bindings.role)"
```

---

## 3. Setting Up the Terraform State File Bucket in GCS

Create a GCS bucket to store the Terraform state files:

```bash
export STATE_BUCKET="$PROJECT_NAME-state"

gcloud storage buckets create "gs://$STATE_BUCKET" \
  --project="$PROJECT_NAME" \
  --location="eu" \
  --default-storage-class="STANDARD" \
  --uniform-bucket-level-access
```

---

## 4. Enable Required APIs in GCP

Use the following commands to enable the required APIs:

```bash
gcloud services enable iamcredentials.googleapis.com \
  --project="$PROJECT_NAME"

gcloud services enable dns.googleapis.com \
  --project="$PROJECT_NAME"
```

---

## 5. Access the Web App

After deployment, access the web app using this URL:

```
http://[YOUR_BUCKET_NAME].storage.googleapis.com
```