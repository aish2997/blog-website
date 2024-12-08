project_id  = "blog-website-d"
region      = "europe-west1"
environment = "dev"

/*
cloud_run_services = {
  "fastapi-backend" = {
    image_suffix = "fastapi-backend:latest"
    environment  = "dev"
  }
}
*/
storage_buckets = {
  "blog-storage" = {
    location = "europe-west1"
    class    = "STANDARD"
    age      = 30
  }
}
/*
bigquery_datasets = {
  "blog_data" = {
    location = "US"
  }
}

bigquery_tables = {
  "blog_posts" = {
    dataset     = "blog_data" # Dataset key from `bigquery_datasets`
    schema_file = "./schema/blog_schema.json"
    partition   = "DAY"
  }
}
*/
/*
cdn_backends = {
  "frontend" = {
    bucket_name = "frontend-static-bucket"
  },
  "blog_assets" = {
    bucket_name = "blog-assets-bucket"
  }
}
*/

/*
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
*/