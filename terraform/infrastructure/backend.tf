terraform {
  backend "gcs" {
    # bucket will be configured via -backend-config in GitHub Actions
    prefix = "infrastructure"
  }
}