region      = "europe-west1"
environment = "prod"

storage_buckets = {
  "blog-storage" = {
    location      = "europe-west1"
    class         = "STANDARD"
    age           = 30
    public_access = true
  }
}