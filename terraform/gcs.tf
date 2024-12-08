resource "google_storage_bucket" "buckets" {
  for_each = var.storage_buckets

  name          = "random-mwmwmwmmwihwefohoewfigho"
  location      = each.value.location
}
