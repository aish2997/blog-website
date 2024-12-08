provider "google" {
  project = var.project_id
  region  = "europe-west1"
  scopes = [
    "https://www.googleapos.com/auth/cloud-platform",
    "https://www.googleapos.com/auth/userinfo.email"
  ]
}