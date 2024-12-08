terraform {
  backend "gcs" {
    bucket  = "blog-website-d-state" # Ensure the bucket exists
    prefix  = "infrastructure/state"
    project = var.project_id
  }
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.12.0"
    }
  }
}
