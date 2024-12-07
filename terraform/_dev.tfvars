project_id  = "my-gcp-project-dev"
region      = "us-central1"
environment = "dev"

cloud_run_services = {
  "fastapi-backend" = {
    image       = "gcr.io/my-gcp-project-dev/fastapi-backend:latest"
    environment = "dev"
  }
}

storage_buckets = {
  "blog-storage" = {
    location = "us-central1"
    class    = "STANDARD"
    age      = 30
  }
}

bigquery_datasets = {
  "blog_data" = {
    location = "US"
  }
}

bigquery_tables = {
  "blog_posts" = {
    schema_file = "database/bigquery_schema.json"
    partition   = "DAY"
  }
}

cdn_backends = {
  "frontend" = {
    bucket_name = "frontend-static-bucket"
  },
  "blog_assets" = {
    bucket_name = "blog-assets-bucket"
  }
}

oauth_clients = {
  "admin_portal" = {
    support_email     = "admin@example.com"
    application_title = "Admin Portal (Dev)"
    client_name       = "admin-oauth-client-dev"
  },
  "user_dashboard" = {
    support_email     = "support@example.com"
    application_title = "User Dashboard"
    client_name       = "user-dashboard-oauth-client-dev"
  }
}
