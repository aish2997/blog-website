resource "google_cloud_run_service" "services" {
  for_each = var.cloud_run_services

  name     = each.key
  location = var.region

  template {
    spec {
      containers {
        image = each.value.image
        env {
          name  = "ENVIRONMENT"
          value = each.value.environment
        }
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }
}