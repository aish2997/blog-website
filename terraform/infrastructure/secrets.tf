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
IMPORTANT: After running Terraform, you must manually add secret values in GCP:

1. Go to Google Cloud Console > Security > Secret Manager
2. Add values for these environment-specific secrets:
   - ${google_secret_manager_secret.django_secret_key.secret_id}: Generate using: python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
   - ${google_secret_manager_secret.django_superuser_username.secret_id}: Your desired admin username
   - ${google_secret_manager_secret.django_superuser_password.secret_id}: A strong password for admin
   - ${google_secret_manager_secret.django_superuser_email.secret_id}: Admin email address
   - ${google_secret_manager_secret.neon_database_url.secret_id}: Your Neon PostgreSQL connection string (postgresql://...)

Note: Secrets are environment-specific (e.g., django-secret-key-staging, django-secret-key-production)
This allows separate credentials for staging and production environments.

3. After adding values, redeploy the Cloud Run service to pick up the secrets
================================================================================
EOF
}