/*
resource "google_storage_bucket" "buckets" {
  for_each = var.storage_buckets

  name          = "${each.key}-${var.environment}"
  location      = each.value.location
  storage_class = each.value.class
}
*/
resource "google_storage_bucket" "example_bucket" {
  name          = "bukcet-blog-website-d-29011997" # Bucket name must be globally unique
  location      = "EU"                             # Replace with the desired location (e.g., US, EU, ASIA)
  force_destroy = true                             # Allows bucket deletion even if it contains objects

  versioning {
    enabled = true # Enable versioning for the bucket
  }

  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      age = 30 # Delete objects older than 30 days
    }
  }

  labels = {
    environment = "dev" # Add labels to the bucket
    team        = "engineering"
  }
}