from fastapi import APIRouter
from backend.database import execute_query
from backend.app.models.comment import Comment
from backend.config import settings
import uuid
from google.cloud import bigquery

router = APIRouter()

@router.get("/{blog_id}")
def get_comments(blog_id: str):
    query = f"""
        SELECT * FROM `{settings.PROJECT_ID}.{settings.DATASET}.{settings.COMMENTS_TABLE}` 
        WHERE blog_id = @blog_id
    """
    comments = execute_query(query, [bigquery.ScalarQueryParameter("blog_id", "STRING", blog_id)])
    return [dict(row) for row in comments]

@router.post("/")
def add_comment(comment: Comment):
    comment_id = str(uuid.uuid4())
    query = f"""
        INSERT INTO `{settings.PROJECT_ID}.{settings.DATASET}.{settings.COMMENTS_TABLE}`
        (id, blog_id, commenter_name, comment_text, created_at)
        VALUES (@id, @blog_id, @commenter_name, @comment_text, @created_at)
    """
    execute_query(query, [
        bigquery.ScalarQueryParameter("id", "STRING", comment_id),
        bigquery.ScalarQueryParameter("blog_id", "STRING", comment.blog_id),
        bigquery.ScalarQueryParameter("commenter_name", "STRING", comment.commenter_name),
        bigquery.ScalarQueryParameter("comment_text", "STRING", comment.comment_text),
        bigquery.ScalarQueryParameter("created_at", "TIMESTAMP", comment.created_at)
    ])
    return {"message": "Comment added successfully", "id": comment_id}
