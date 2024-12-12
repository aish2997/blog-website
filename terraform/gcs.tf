resource "google_storage_bucket" "blog_bucket" {
  for_each = var.storage_buckets

  #name          = "${each.key}-${var.environment}"
  name          = each.key == "blog-storage" && var.environment == "prod" ? "www.aishwaryabhargava.com" : "${each.key}-${var.environment}"
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

resource "google_storage_bucket_iam_member" "all_users_viewer" {
  for_each = { for key, bucket in var.storage_buckets : key => bucket if bucket.public_access }

  bucket = google_storage_bucket.blog_bucket[each.key].name
  role   = "roles/storage.objectViewer"
  member = "allUsers"
}