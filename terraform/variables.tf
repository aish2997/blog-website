variable "project_id" {
  type        = string
  description = "GCP project ID"
}

variable "region" {
  type        = string
  description = "GCP region"
}

variable "environment" {
  type        = string
  description = "Deployment environment (dev/test/prod)"
}

variable "storage_buckets" {
  type = map(object({
    location      = string
    class         = string
    age           = number
    public_access = bool
  }))
  description = "Configuration for GCS buckets, including public access option"
}