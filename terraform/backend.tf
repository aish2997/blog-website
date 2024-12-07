terraform {
  backend "gcs" {
    prefix = "infrastructure/state"
    project = var.project_id
  }
}
