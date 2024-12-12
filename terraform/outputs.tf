output "public_buckets" {
  value = [
    for key, bucket in var.storage_buckets :
    google_storage_bucket.blog_bucket[key].name
    if bucket.public_access
  ]
  description = "List of public buckets with allUsers role"
}
