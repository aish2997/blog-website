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
/*
variable "cloud_run_services" {
  type = map(object({
    image_suffix = string
    environment  = string
  }))
  description = "Configuration for Cloud Run services"
}
*/

variable "storage_buckets" {
  type = map(object({
    location = string
    class    = string
    age      = number
  }))
  description = "Configuration for GCS buckets"
}

variable "bigquery_datasets" {
  type = map(object({
    location = string
  }))
  description = "Configuration for BigQuery datasets"
}

variable "bigquery_tables" {
  type = map(object({
    dataset     = string # Reference to the dataset name
    schema_file = string
    partition   = string
  }))
  description = "Configuration for BigQuery tables"
}

/*
variable "cdn_backends" {
  description = "Map of CDN backends with their bucket configurations"
  type = map(object({
    bucket_name = string
  }))
  default = {
    "frontend" = {
      bucket_name = "frontend-static-bucket"
    },
    "blog_assets" = {
      bucket_name = "blog-assets-bucket"
    }
  }
}
*/
/*
variable "oauth_clients" {
  description = "Map of OAuth clients with their configuration details"
  type = map(object({
    support_email     = string
    application_title = string
    client_name       = string
  }))
  default = {
    "admin_portal" = {
      support_email     = "admin@example.com"
      application_title = "Admin Portal"
      client_name       = "admin-oauth-client"
    }
  }
}
*/