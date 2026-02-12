# Secret Manager secrets for Django application
# These create the secret containers - you'll need to add values manually in GCP Console

# Django SECRET_KEY - critical for security
resource "google_secret_manager_secret" "django_secret_key" {
  secret_id = "django-secret-key-${var.environment}"

  labels = {
    environment = var.environment
    managed_by  = "terraform"
    purpose     = "django-security"
  }

  replication {
    auto {}
  }
}

# Django superuser credentials
resource "google_secret_manager_secret" "django_superuser_username" {
  secret_id = "django-superuser-username-${var.environment}"

  labels = {
    environment = var.environment
    managed_by  = "terraform"
    purpose     = "admin-access"
  }

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "django_superuser_password" {
  secret_id = "django-superuser-password-${var.environment}"

  labels = {
    environment = var.environment
    managed_by  = "terraform"
    purpose     = "admin-access"
  }

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "django_superuser_email" {
  secret_id = "django-superuser-email-${var.environment}"

  labels = {
    environment = var.environment
    managed_by  = "terraform"
    purpose     = "admin-access"
  }

  replication {
    auto {}
  }
}

# Neon PostgreSQL database connection URL
resource "google_secret_manager_secret" "neon_database_url" {
  secret_id = "neon-database-url-${var.environment}"

  labels = {
    environment = var.environment
    managed_by  = "terraform"
    purpose     = "database-connection"
  }

  replication {
    auto {}
  }
}

# Secret versions - populate secrets with actual values from CI/CD
resource "google_secret_manager_secret_version" "django_secret_key" {
  secret      = google_secret_manager_secret.django_secret_key.id
  secret_data = var.django_secret_key
}

resource "google_secret_manager_secret_version" "neon_database_url" {
  secret      = google_secret_manager_secret.neon_database_url.id
  secret_data = var.neon_database_url
}

resource "google_secret_manager_secret_version" "django_superuser_username" {
  secret      = google_secret_manager_secret.django_superuser_username.id
  secret_data = var.django_superuser_username
}

resource "google_secret_manager_secret_version" "django_superuser_password" {
  secret      = google_secret_manager_secret.django_superuser_password.id
  secret_data = var.django_superuser_password
}

resource "google_secret_manager_secret_version" "django_superuser_email" {
  secret      = google_secret_manager_secret.django_superuser_email.id
  secret_data = var.django_superuser_email
}

# Grant the Cloud Run service account access to read these secrets
resource "google_secret_manager_secret_iam_member" "django_secret_key_access" {
  secret_id = google_secret_manager_secret.django_secret_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${data.google_service_account.cloud_run.email}"
}

resource "google_secret_manager_secret_iam_member" "django_superuser_username_access" {
  secret_id = google_secret_manager_secret.django_superuser_username.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${data.google_service_account.cloud_run.email}"
}

resource "google_secret_manager_secret_iam_member" "django_superuser_password_access" {
  secret_id = google_secret_manager_secret.django_superuser_password.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${data.google_service_account.cloud_run.email}"
}

resource "google_secret_manager_secret_iam_member" "django_superuser_email_access" {
  secret_id = google_secret_manager_secret.django_superuser_email.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${data.google_service_account.cloud_run.email}"
}

resource "google_secret_manager_secret_iam_member" "neon_database_url_access" {
  secret_id = google_secret_manager_secret.neon_database_url.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${data.google_service_account.cloud_run.email}"
}

# Output the secret names for reference
output "secret_instructions" {
  value = <<EOF
================================================================================
Secret Manager secrets are automatically populated from CI/CD pipeline variables.

Environment-specific secrets managed:
   - ${google_secret_manager_secret.django_secret_key.secret_id}
   - ${google_secret_manager_secret.django_superuser_username.secret_id}
   - ${google_secret_manager_secret.django_superuser_password.secret_id}
   - ${google_secret_manager_secret.django_superuser_email.secret_id}
   - ${google_secret_manager_secret.neon_database_url.secret_id}

To update secret values, update the corresponding GitHub repository secrets
and re-run the deployment workflow.
================================================================================
EOF
}