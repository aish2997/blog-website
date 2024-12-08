/*
resource "google_storage_bucket" "buckets" {
  for_each = var.storage_buckets

  name          = "${each.key}-${var.environment}"
  location      = each.value.location
  storage_class = each.value.class
}
*/

resource "google_storage_bucket" "example_bucket" {
  name     = "your-unique-bucket-name-29292992" # Follow naming rules
  location = "EU"                     # Ensure location is valid
  project  = "blog-website-d"    # Correct project ID
}
