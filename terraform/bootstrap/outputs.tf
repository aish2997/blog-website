output "state_bucket" {
  description = "GCS bucket for Terraform state"
  value       = google_storage_bucket.terraform_state.name
}

output "artifact_registry_repository" {
  description = "Artifact Registry repository for Docker images"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.docker_repo.repository_id}"
}

output "workload_identity_provider" {
  description = "Workload Identity Provider for GitHub Actions"
  value       = "projects/${data.google_project.project.number}/locations/global/workloadIdentityPools/${google_iam_workload_identity_pool.github_pool.workload_identity_pool_id}/providers/${google_iam_workload_identity_pool_provider.github_provider.workload_identity_pool_provider_id}"
}

output "github_actions_service_account" {
  description = "Service account email for GitHub Actions"
  value       = google_service_account.github_actions.email
}

output "cloud_run_service_account" {
  description = "Service account email for Cloud Run"
  value       = google_service_account.cloud_run.email
}

data "google_project" "project" {
  project_id = var.project_id
}