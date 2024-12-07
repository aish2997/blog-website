terraform {
  backend "gcs" {
    bucket  = "YOUR_BUCKET_NAME"
    prefix = "${var.environment}/terraform/state"
    project = var.project_id
  }
}
