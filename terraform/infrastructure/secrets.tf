# Secret Manager secrets for Django application
# These create the secret containers - you'll need to add values manually in GCP Console

# Django SECRET_KEY - critical for security
resource "google_secret_manager_secret" "django_secret_key" {
  secret_id = "django-secret-key"

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
  secret_id = "django-superuser-username"

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
  secret_id = "django-superuser-password"

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
  secret_id = "django-superuser-email"

  labels = {
    environment = var.environment
    managed_by  = "terraform"
    purpose     = "admin-access"
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

# Output the secret names for reference
output "secret_instructions" {
  value = <<EOF
================================================================================
IMPORTANT: After running Terraform, you must manually add secret values in GCP:

1. Go to Google Cloud Console > Security > Secret Manager
2. Add values for these secrets:
   - ${google_secret_manager_secret.django_secret_key.name}: Generate using: python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
   - ${google_secret_manager_secret.django_superuser_username.name}: Your desired admin username
   - ${google_secret_manager_secret.django_superuser_password.name}: A strong password for admin
   - ${google_secret_manager_secret.django_superuser_email.name}: Admin email address

3. After adding values, redeploy the Cloud Run service to pick up the secrets
================================================================================
EOF
}