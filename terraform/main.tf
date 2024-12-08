provider "google" {
  project                     = "blog-website-d"
  region                      = "europe-west1"
  impersonate_service_account = "github-actions-sa@blog-website-d.iam.gserviceaccount.com"

}