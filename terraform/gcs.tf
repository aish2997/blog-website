resource "google_storage_bucket" "blog_bucket" {
  for_each = var.storage_buckets

  name          = "www.aishwaryabhargava.com"
  location      = each.value.location
  storage_class = each.value.class

  website {
    main_page_suffix = "index.html"
    not_found_page   = "404.html"
  }

  lifecycle {
    prevent_destroy = false # Allows the bucket to be destroyed if needed
  }
}
