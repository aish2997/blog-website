provider "google" {
  project = "blog-website-d"
  region  = "europe-west1"
  scopes = [
    "https://www.googleapos.com/auth/cloud-platform",
    "https://www.googleapos.com/auth/userinfo.email"
  ]
}