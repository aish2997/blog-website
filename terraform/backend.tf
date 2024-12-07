terraform {
  backend "gcs" {
    bucket  = "YOUR_BUCKET_NAME"
    prefix = "terraform/state"
    project = var.project_id
  }
}
