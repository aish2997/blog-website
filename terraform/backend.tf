terraform {
  backend "gcs" {
    bucket  = "blog-website-d" # Ensure the bucket exists
    prefix  = "infrastructure/state"
    project = var.project_id
  }

}
