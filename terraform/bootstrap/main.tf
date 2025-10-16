terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Enable required APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "iam.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "iamcredentials.googleapis.com",
    "sts.googleapis.com",
    "artifactregistry.googleapis.com",
    "run.googleapis.com",
    "sqladmin.googleapis.com",
    "compute.googleapis.com",
    "secretmanager.googleapis.com",
    "storage.googleapis.com",
    "cloudbuild.googleapis.com",
  ])

  service            = each.value
  disable_on_destroy = false
}

# Create Terraform state bucket
resource "google_storage_bucket" "terraform_state" {
  name     = "${var.project_id}-terraform-state"
  location = var.region

  versioning {
    enabled = true
  }

  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      num_newer_versions = 5
      with_state         = "ARCHIVED"
    }
  }

  uniform_bucket_level_access = true

  labels = {
    environment = var.environment
    managed_by  = "terraform"
  }

  depends_on = [google_project_service.required_apis]
}

# Create Artifact Registry for Docker images
resource "google_artifact_registry_repository" "docker_repo" {
  repository_id = "portfolio-images"
  format        = "DOCKER"
  location      = var.region
  description   = "Docker repository for portfolio application images"

  labels = {
    environment = var.environment
    managed_by  = "terraform"
  }

  depends_on = [google_project_service.required_apis]
}

# Create Workload Identity Pool
resource "google_iam_workload_identity_pool" "github_pool" {
  workload_identity_pool_id = "github-pool-2"
  display_name              = "GitHub Actions Pool"
  description              = "Workload Identity Pool for GitHub Actions"

  depends_on = [google_project_service.required_apis]
}

# Create Workload Identity Provider
resource "google_iam_workload_identity_pool_provider" "github_provider" {
  workload_identity_pool_id          = google_iam_workload_identity_pool.github_pool.workload_identity_pool_id
  workload_identity_pool_provider_id = "github-provider"
  display_name                       = "GitHub Provider"
  description                        = "OIDC provider for GitHub Actions"

  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.actor"      = "assertion.actor"
    "attribute.repository" = "assertion.repository"
    "attribute.repository_owner" = "assertion.repository_owner"
  }

  attribute_condition = "assertion.repository_owner == '${var.github_owner}'"

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

# Service Account for GitHub Actions
resource "google_service_account" "github_actions" {
  account_id   = "github-actions-sa"
  display_name = "GitHub Actions Service Account"
  description  = "Service account for GitHub Actions CI/CD"
}

# Service Account for Cloud Run
resource "google_service_account" "cloud_run" {
  account_id   = "portfolio-cloud-run-sa"
  display_name = "Portfolio Cloud Run Service Account"
  description  = "Service account for Cloud Run portfolio application"
}

# Grant GitHub Actions SA necessary permissions
resource "google_project_iam_member" "github_actions_roles" {
  for_each = toset([
    "roles/run.admin",
    "roles/storage.admin",
    "roles/artifactregistry.writer",
    "roles/cloudsql.admin",
    "roles/secretmanager.admin",
    "roles/iam.serviceAccountUser",
    "roles/compute.networkAdmin",
    "roles/resourcemanager.projectIamAdmin",
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.github_actions.email}"
}

# Grant Cloud Run SA necessary permissions
resource "google_project_iam_member" "cloud_run_roles" {
  for_each = toset([
    "roles/cloudsql.client",
    "roles/storage.objectAdmin",
    "roles/secretmanager.secretAccessor",
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.cloud_run.email}"
}

# Allow GitHub Actions to impersonate the service account
resource "google_service_account_iam_binding" "github_actions_impersonation" {
  service_account_id = google_service_account.github_actions.name
  role              = "roles/iam.workloadIdentityUser"

  members = [
    "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github_pool.name}/attribute.repository/${var.github_owner}/${var.github_repository}"
  ]
}

# Create initial secrets in Secret Manager
resource "google_secret_manager_secret" "django_secret_key" {
  secret_id = "django-secret-key"

  replication {
    auto {}
  }

  labels = {
    environment = var.environment
    managed_by  = "terraform"
  }

  depends_on = [google_project_service.required_apis]
}

resource "google_secret_manager_secret" "db_password" {
  secret_id = "db-password"

  replication {
    auto {}
  }

  labels = {
    environment = var.environment
    managed_by  = "terraform"
  }

  depends_on = [google_project_service.required_apis]
}

# Generate random passwords for secrets (initial values)
resource "random_password" "django_secret_key" {
  length  = 50
  special = true
}

resource "random_password" "db_password" {
  length  = 32
  special = true
}

# Create secret versions
resource "google_secret_manager_secret_version" "django_secret_key" {
  secret      = google_secret_manager_secret.django_secret_key.id
  secret_data = random_password.django_secret_key.result
}

resource "google_secret_manager_secret_version" "db_password" {
  secret      = google_secret_manager_secret.db_password.id
  secret_data = random_password.db_password.result
}