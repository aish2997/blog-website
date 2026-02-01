terraform {
  backend "gcs" {
    # bucket and prefix will be configured via -backend-config in GitHub Actions
    # prefix format: infrastructure-{environment} (e.g., infrastructure-staging, infrastructure-production)
  }
}