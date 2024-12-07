backend "gcs" {
  bucket  = "blog-website-d-state"  # Ensure the bucket exists
  prefix  = "terraform/state"
  project = var.project_id
}
