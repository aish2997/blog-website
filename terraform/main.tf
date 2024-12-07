provider "google" {
  project = "your-gcp-project-id"
  region  = "us-central1"
}

resource "google_storage_bucket" "blog_assets" {
  name          = "blog-assets-bucket"
  location      = "US"
  force_destroy = true
}
