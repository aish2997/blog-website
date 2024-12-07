import os

class Settings:
    PROJECT_ID = os.getenv("GCP_PROJECT_ID", "your-project-id")
    DATASET = os.getenv("BIGQUERY_DATASET", "blog_data")
    BLOGS_TABLE = "blogs"
    COMMENTS_TABLE = "comments"
    VISITORS_TABLE = "visitors"

settings = Settings()
