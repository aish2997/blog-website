variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Environment name (e.g., production, staging)"
  type        = string
  default     = "production"
}

variable "domain" {
  description = "Custom domain for the application (optional)"
  type        = string
  default     = ""
}

# Cloud Run Configuration
variable "cloud_run_cpu" {
  description = "CPU allocation for Cloud Run"
  type        = string
  default     = "1"
}

variable "cloud_run_memory" {
  description = "Memory allocation for Cloud Run"
  type        = string
  default     = "1Gi"
}

variable "cloud_run_max_instances" {
  description = "Maximum number of Cloud Run instances (set to 1 for SQLite)"
  type        = number
  default     = 1
}

variable "cloud_run_min_instances" {
  description = "Minimum number of Cloud Run instances"
  type        = number
  default     = 0
}

# Application Configuration
variable "django_settings_module" {
  description = "Django settings module to use"
  type        = string
  default     = "portfolio.settings_production"
}

variable "django_allowed_hosts" {
  description = "Django ALLOWED_HOSTS setting - must be explicitly configured for production"
  type        = string
  # No default - must be explicitly set for security
}

# Docker Image
variable "docker_image" {
  description = "Docker image to deploy"
  type        = string
}

# Secret Values (passed from CI/CD pipeline)
variable "django_secret_key" {
  description = "Django SECRET_KEY"
  type        = string
  sensitive   = true

  validation {
    condition     = length(var.django_secret_key) >= 50
    error_message = "django_secret_key must be at least 50 characters. Check DJANGO_SECRET_KEY_STAGING (or _PRODUCTION) in GitHub Actions secrets."
  }
}

variable "neon_database_url" {
  description = "Neon PostgreSQL connection URL"
  type        = string
  sensitive   = true

  validation {
    condition     = length(var.neon_database_url) > 0
    error_message = "neon_database_url must not be empty. Check NEON_DATABASE_URL_STAGING (or _PRODUCTION) in GitHub Actions secrets."
  }
}

variable "django_superuser_username" {
  description = "Django superuser username"
  type        = string
  sensitive   = true
}

variable "django_superuser_password" {
  description = "Django superuser password"
  type        = string
  sensitive   = true
}

variable "django_superuser_email" {
  description = "Django superuser email"
  type        = string
  sensitive   = true
}