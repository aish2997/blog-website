terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
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

data "google_secret_manager_secret" "db_password" {
  secret_id = "db-password"
}

# VPC for Cloud SQL
resource "google_compute_network" "vpc" {
  name                    = "portfolio-vpc-${var.environment}"
  auto_create_subnetworks = false

  description = "VPC network for portfolio application"
}

resource "google_compute_subnetwork" "subnet" {
  name          = "portfolio-subnet-${var.environment}"
  ip_cidr_range = "10.0.0.0/24"
  network       = google_compute_network.vpc.id
  region        = var.region

  private_ip_google_access = true
}

# VPC Connector for Cloud Run to access Cloud SQL
resource "google_vpc_access_connector" "connector" {
  name          = "portfolio-con-${var.environment}"
  region        = var.region
  network       = google_compute_network.vpc.name
  ip_cidr_range = "10.1.0.0/28"

  min_instances = 2
  max_instances = 3
}

# Cloud SQL Instance
resource "google_sql_database_instance" "postgres" {
  name             = "portfolio-db-${var.environment}"
  database_version = var.database_version
  region           = var.region

  settings {
    tier              = var.database_tier
    availability_type = "ZONAL"

    backup_configuration {
      enabled                        = var.database_backup_enabled
      start_time                     = "02:00"
      point_in_time_recovery_enabled = var.database_backup_enabled
      transaction_log_retention_days = var.database_backup_enabled ? 7 : 0

      backup_retention_settings {
        retained_backups = 7
        retention_unit   = "COUNT"
      }
    }

    ip_configuration {
      ipv4_enabled                                  = false
      private_network                               = google_compute_network.vpc.id
      enable_private_path_for_google_cloud_services = true
    }

    database_flags {
      name  = "max_connections"
      value = "100"
    }

    insights_config {
      query_insights_enabled  = true
      query_string_length     = 1024
      record_application_tags = true
      record_client_address   = true
    }
  }

  deletion_protection = var.environment == "production"

  depends_on = [google_service_networking_connection.private_vpc_connection]
}

# Private IP for Cloud SQL
resource "google_compute_global_address" "private_ip" {
  name          = "portfolio-db-ip-${var.environment}"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.vpc.id
}

resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.vpc.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip.name]
}

# Database
resource "google_sql_database" "database" {
  name     = "portfolio"
  instance = google_sql_database_instance.postgres.name
}

# Database User
resource "google_sql_user" "user" {
  name     = "portfolio_user"
  instance = google_sql_database_instance.postgres.name
  password = data.google_secret_manager_secret_version.db_password.secret_data
}

data "google_secret_manager_secret_version" "db_password" {
  secret = data.google_secret_manager_secret.db_password.id
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

  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }

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
          name  = "DATABASE_URL"
          value = "postgresql://${google_sql_user.user.name}:${data.google_secret_manager_secret_version.db_password.secret_data}@/${google_sql_database.database.name}?host=/cloudsql/${google_sql_database_instance.postgres.connection_name}"
        }

        env {
          name  = "CLOUD_SQL_CONNECTION_NAME"
          value = google_sql_database_instance.postgres.connection_name
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
          name = "SECRET_KEY"
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
          name  = "USE_CLOUD_SQL_PROXY"
          value = "False"
        }
      }
    }

    metadata {
      annotations = {
        "autoscaling.knative.dev/maxScale"         = tostring(var.cloud_run_max_instances)
        "autoscaling.knative.dev/minScale"         = tostring(var.cloud_run_min_instances)
        "run.googleapis.com/cloudsql-instances"    = google_sql_database_instance.postgres.connection_name
        "run.googleapis.com/vpc-access-connector"  = google_vpc_access_connector.connector.id
        "run.googleapis.com/vpc-access-egress"     = "private-ranges-only"
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