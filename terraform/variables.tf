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

variable "cloud_run_services" {
  type        = map(object({
    image       = string
    environment = string
  }))
  description = "Configuration for Cloud Run services"
}

variable "storage_buckets" {
  type        = map(object({
    location = string
    class    = string
    age      = number
  }))
  description = "Configuration for GCS buckets"
}

variable "bigquery_datasets" {
  type        = map(object({
    location = string
  }))
  description = "Configuration for BigQuery datasets"
}

variable "bigquery_tables" {
  type        = map(object({
    schema_file = string
    partition   = string
  }))
  description = "Configuration for BigQuery tables"
}
