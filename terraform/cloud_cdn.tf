/*
resource "google_compute_backend_bucket" "cdn_backends" {
  for_each = var.cdn_backends

  name        = "${each.key}-cdn"
  bucket_name = each.value.bucket_name
  enable_cdn  = true
}
*/
