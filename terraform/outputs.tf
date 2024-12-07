output "cloud_run_url" {
  description = "The URL of the Cloud Run service"
  value       = google_cloud_run_service.backend.status[0].url
}

output "cdn_backend" {
  description = "The Cloud CDN backend URL"
  value       = google_compute_backend_bucket.cdn_backend.bucket_name
}
