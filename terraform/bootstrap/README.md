# Bootstrap Infrastructure

This directory contains Terraform configuration for bootstrapping the initial GCP infrastructure required for the portfolio blog website.

## Prerequisites

### 1. Manual API Enablement

Due to GCP's bootstrap requirements, you must manually enable the following APIs in the Google Cloud Console **before** running the bootstrap workflow:

1. **Service Usage API**
   - Required for enabling other APIs programmatically
   - Enable at: `https://console.cloud.google.com/apis/library/serviceusage.googleapis.com?project=YOUR_PROJECT_ID`

2. **Cloud Resource Manager API**
   - Required for managing project resources
   - Enable at: `https://console.cloud.google.com/apis/library/cloudresourcemanager.googleapis.com?project=YOUR_PROJECT_ID`

3. **IAM API**
   - Required for managing service accounts and permissions
   - Enable at: `https://console.cloud.google.com/apis/library/iam.googleapis.com?project=YOUR_PROJECT_ID`

### 2. Service Account Setup

1. Create an initial service account in your GCP project with the following roles:
   - `roles/owner` (temporarily, for bootstrap only)
   - Or at minimum:
     - `roles/iam.admin`
     - `roles/storage.admin`
     - `roles/serviceusage.admin`
     - `roles/resourcemanager.projectIamAdmin`

2. Generate and download a JSON key for this service account

3. Add the JSON key content as a GitHub secret named `GCP_SA_KEY`

## Running the Bootstrap Workflow

1. Go to your GitHub repository
2. Navigate to Actions → Bootstrap Infrastructure
3. Click "Run workflow"
4. Fill in the required parameters:
   - **Project ID**: Your GCP project ID (e.g., `blog-website-d`)
   - **Region**: Your preferred GCP region (default: `us-central1`)
   - **GitHub Owner**: Your GitHub username or organization
   - **GitHub Repository**: Your repository name (e.g., `blog-website`)

## What Gets Created

The bootstrap process creates:

- **Terraform State Bucket**: For storing Terraform state files
- **Artifact Registry**: For Docker images
- **Workload Identity Federation**: For GitHub Actions authentication
- **Service Accounts**:
  - `github-actions-sa`: For CI/CD operations
  - `portfolio-cloud-run-sa`: For the application runtime
- **Secret Manager Secrets**: For Django secret key and database password
- **Enabled APIs**: All required GCP APIs for the application

## Outputs

After successful bootstrap, the workflow will display:

- State bucket name (for Terraform backend configuration)
- Artifact Registry repository URL
- Workload Identity Provider (for GitHub Actions)
- Service account email addresses

## Next Steps

After bootstrap completes:

1. Note the outputs from the workflow summary
2. Configure the following GitHub repository secrets:
   - `WIF_PROVIDER`: The Workload Identity Provider value
   - `WIF_SERVICE_ACCOUNT`: The GitHub Actions service account email
   - `GCP_PROJECT_ID`: Your project ID
   - `GCP_REGION`: Your chosen region
   - `TF_STATE_BUCKET`: The state bucket name

3. Run the deployment workflow to deploy the application

## Troubleshooting

### "Service Usage API has not been used" Error

If you see this error, it means the prerequisite APIs haven't been enabled manually. Follow the links provided in the error message to enable them in the Google Cloud Console.

### "Permission Denied" Errors

Ensure your service account (used in `GCP_SA_KEY`) has sufficient permissions. The account needs to be able to:
- Enable APIs
- Create service accounts
- Create storage buckets
- Manage IAM policies

### Terraform State Issues

If you need to re-run bootstrap after a partial failure:
1. Check if resources were partially created in GCP Console
2. Either manually delete them or import them into Terraform state
3. Re-run the workflow

## Security Notes

- The `GCP_SA_KEY` secret should be removed or replaced with Workload Identity Federation after bootstrap
- The initial service account's permissions can be reduced after bootstrap
- Consider using separate projects for different environments (dev, staging, prod)