variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

variable "github_owner" {
  description = "GitHub repository owner (username or organization)"
  type        = string
}

variable "github_repository" {
  description = "GitHub repository name"
  type        = string
}

variable "environment" {
  description = "Environment name (e.g., production, staging)"
  type        = string
  default     = "production"
}