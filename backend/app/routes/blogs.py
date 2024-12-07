from fastapi import APIRouter, HTTPException
from backend.database import execute_query
from backend.app.models.blog import Blog
from backend.config import settings
import uuid
from google.cloud import bigquery

router = APIRouter()

@router.get("/")
def get_blogs():
    query = f"SELECT * FROM `{settings.PROJECT_ID}.{settings.DATASET}.{settings.BLOGS_TABLE}`"
    blogs = execute_query(query)
    return [dict(row) for row in blogs]

@router.post("/")
def create_blog(blog: Blog):
    blog_id = str(uuid.uuid4())
    query = f"""
        INSERT INTO `{settings.PROJECT_ID}.{settings.DATASET}.{settings.BLOGS_TABLE}` 
        (id, title, content, tags, created_at) 
        VALUES (@id, @title, @content, @tags, @created_at)
    """
    execute_query(query, [
        bigquery.ScalarQueryParameter("id", "STRING", blog_id),
        bigquery.ScalarQueryParameter("title", "STRING", blog.title),
        bigquery.ScalarQueryParameter("content", "STRING", blog.content),
        bigquery.ScalarQueryParameter("tags", "ARRAY<STRING>", blog.tags),
        bigquery.ScalarQueryParameter("created_at", "TIMESTAMP", blog.created_at)
    ])
    return {"message": "Blog created successfully", "id": blog_id}
