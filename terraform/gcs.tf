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

  cors {
    origins          = ["*"]
    methods          = ["GET", "HEAD"]
    response_headers = ["Content-Type"]
    max_age_seconds  = 3600
  }
}

# Grant 'allUsers' permission to read the contents of the bucket
resource "google_storage_bucket_object" "public_index" {
  bucket = google_storage_bucket.blog_bucket.name
  name   = "index.html"
  source = "blog-storage-dev/index.html" # Replace with your local file path
}

resource "google_storage_bucket_object" "public_404" {
  bucket = google_storage_bucket.blog_bucket.name
  name   = "404.html"
  source = "blog-storage-dev/404.html" # Replace with your local file path
}

resource "google_storage_bucket_iam_binding" "bucket_all_users" {
  bucket = google_storage_bucket.blog_bucket.name

  role    = "roles/storage.objectViewer"
  members = ["allUsers"]
}