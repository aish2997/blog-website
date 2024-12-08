resource "google_storage_bucket" "buckets" {
  for_each = var.storage_buckets

  name          = "${each.key}-${var.environment}"
  location      = each.value.location
  storage_class = each.value.class
}
