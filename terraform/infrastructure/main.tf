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

# Data sources for existing resources created by bootstrap
data "google_service_account" "cloud_run" {
  account_id = "portfolio-cloud-run-sa"
}

data "google_secret_manager_secret" "django_secret_key" {
  secret_id = "django-secret-key"
}

# Superuser credentials secrets
resource "google_secret_manager_secret" "django_superuser_username" {
  secret_id = "django-superuser-username"

  replication {
    auto {}
  }

  labels = {
    environment = var.environment
    managed_by  = "terraform"
  }
}

resource "google_secret_manager_secret" "django_superuser_email" {
  secret_id = "django-superuser-email"

  replication {
    auto {}
  }

  labels = {
    environment = var.environment
    managed_by  = "terraform"
  }
}

resource "google_secret_manager_secret" "django_superuser_password" {
  secret_id = "django-superuser-password"

  replication {
    auto {}
  }

  labels = {
    environment = var.environment
    managed_by  = "terraform"
  }
}

# Create initial secret versions with default values (to be updated manually)
resource "google_secret_manager_secret_version" "django_superuser_username" {
  secret      = google_secret_manager_secret.django_superuser_username.id
  secret_data = var.django_superuser_username != "" ? var.django_superuser_username : "admin"
}

resource "google_secret_manager_secret_version" "django_superuser_email" {
  secret      = google_secret_manager_secret.django_superuser_email.id
  secret_data = var.django_superuser_email != "" ? var.django_superuser_email : "admin@example.com"
}

resource "google_secret_manager_secret_version" "django_superuser_password" {
  secret      = google_secret_manager_secret.django_superuser_password.id
  secret_data = var.django_superuser_password != "" ? var.django_superuser_password : "CHANGE_THIS_PASSWORD"
}

# Cloud Storage Buckets
resource "google_storage_bucket" "media" {
  name     = "${var.project_id}-portfolio-media-${var.environment}"
  location = var.region

  uniform_bucket_level_access = true

  cors {
    origin          = ["*"]
    method          = ["GET", "HEAD"]
    response_header = ["*"]
    max_age_seconds = 3600
  }

  # No lifecycle rule - media files should be kept indefinitely

  labels = {
    environment = var.environment
    managed_by  = "terraform"
  }
}

resource "google_storage_bucket" "static" {
  name     = "${var.project_id}-portfolio-static-${var.environment}"
  location = var.region

  uniform_bucket_level_access = true

  cors {
    origin          = ["*"]
    method          = ["GET", "HEAD"]
    response_header = ["*"]
    max_age_seconds = 86400
  }

  labels = {
    environment = var.environment
    managed_by  = "terraform"
  }
}

# Make buckets publicly readable
resource "google_storage_bucket_iam_member" "media_public" {
  bucket = google_storage_bucket.media.name
  role   = "roles/storage.objectViewer"
  member = "allUsers"
}

resource "google_storage_bucket_iam_member" "static_public" {
  bucket = google_storage_bucket.static.name
  role   = "roles/storage.objectViewer"
  member = "allUsers"
}

# Cloud Run Service
resource "google_cloud_run_service" "portfolio" {
  name     = "portfolio-${var.environment}"
  location = var.region

  template {
    spec {
      service_account_name = data.google_service_account.cloud_run.email

      containers {
        image = var.docker_image

        ports {
          container_port = 8080
        }

        resources {
          limits = {
            cpu    = var.cloud_run_cpu
            memory = var.cloud_run_memory
          }
        }

        env {
          name  = "DJANGO_SETTINGS_MODULE"
          value = var.django_settings_module
        }

        env {
          name  = "GCP_PROJECT_ID"
          value = var.project_id
        }

        env {
          name  = "ALLOWED_HOSTS"
          value = var.django_allowed_hosts
        }

        env {
          name  = "GCS_BUCKET_MEDIA"
          value = google_storage_bucket.media.name
        }

        env {
          name  = "GCS_BUCKET_STATIC"
          value = google_storage_bucket.static.name
        }

        env {
          name  = "SECRET_KEY"
          value_from {
            secret_key_ref {
              name = data.google_secret_manager_secret.django_secret_key.secret_id
              key  = "latest"
            }
          }
        }

        env {
          name  = "DEBUG"
          value = "False"
        }

        env {
          name  = "DATABASE_PATH"
          value = "/tmp/db.sqlite3"
        }

        # Superuser credentials from Secret Manager
        env {
          name = "DJANGO_SUPERUSER_USERNAME"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.django_superuser_username.secret_id
              key  = "latest"
            }
          }
        }

        env {
          name = "DJANGO_SUPERUSER_EMAIL"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.django_superuser_email.secret_id
              key  = "latest"
            }
          }
        }

        env {
          name = "DJANGO_SUPERUSER_PASSWORD"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.django_superuser_password.secret_id
              key  = "latest"
            }
          }
        }
      }
    }

    metadata {
      annotations = {
        "autoscaling.knative.dev/maxScale"         = tostring(var.cloud_run_max_instances)
        "autoscaling.knative.dev/minScale"         = tostring(var.cloud_run_min_instances)
        "run.googleapis.com/execution-environment" = "gen2"
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  autogenerate_revision_name = true

  lifecycle {
    ignore_changes = [
      template[0].metadata[0].annotations["run.googleapis.com/client-name"],
      template[0].metadata[0].annotations["run.googleapis.com/client-version"],
    ]
  }
}

# Make Cloud Run service publicly accessible
resource "google_cloud_run_service_iam_member" "public" {
  service  = google_cloud_run_service.portfolio.name
  location = google_cloud_run_service.portfolio.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Cloud Run Domain Mapping (if custom domain is provided)
resource "google_cloud_run_domain_mapping" "domain" {
  count    = var.domain != "" ? 1 : 0
  name     = var.domain
  location = google_cloud_run_service.portfolio.location

  metadata {
    namespace = var.project_id
  }

  spec {
    route_name = google_cloud_run_service.portfolio.name
  }
}