output "cloud_run_url" {
  description = "URL of the Cloud Run service"
  value       = google_cloud_run_service.portfolio.status[0].url
}

output "media_bucket" {
  description = "GCS bucket for media files"
  value       = google_storage_bucket.media.name
}

output "static_bucket" {
  description = "GCS bucket for static files"
  value       = google_storage_bucket.static.name
}

output "service_name" {
  description = "Name of the Cloud Run service"
  value       = google_cloud_run_service.portfolio.name
}

output "custom_domain" {
  description = "Custom domain if configured"
  value       = var.domain != "" ? var.domain : "Not configured"
}