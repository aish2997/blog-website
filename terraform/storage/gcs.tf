resource "google_storage_bucket" "buckets" {
  for_each = var.storage_buckets

  name          = "${each.key}-${var.environment}"
  location      = each.value.location
  storage_class = each.value.class

  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      age = each.value.age
    }
  }

  uniform_bucket_level_access = true
}
