output "cloud_run_url" {
  description = "URL of the Cloud Run service"
  value       = google_cloud_run_service.portfolio.status[0].url
}

output "cloud_sql_instance_name" {
  description = "Name of the Cloud SQL instance"
  value       = google_sql_database_instance.postgres.name
}

output "cloud_sql_connection_name" {
  description = "Connection name for Cloud SQL"
  value       = google_sql_database_instance.postgres.connection_name
}

output "media_bucket" {
  description = "GCS bucket for media files"
  value       = google_storage_bucket.media.name
}

output "static_bucket" {
  description = "GCS bucket for static files"
  value       = google_storage_bucket.static.name
}

output "vpc_connector" {
  description = "VPC connector for Cloud Run"
  value       = google_vpc_access_connector.connector.id
}

output "service_name" {
  description = "Name of the Cloud Run service"
  value       = google_cloud_run_service.portfolio.name
}

output "custom_domain" {
  description = "Custom domain if configured"
  value       = var.domain != "" ? var.domain : "Not configured"
}