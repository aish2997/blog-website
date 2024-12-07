from fastapi import APIRouter
from backend.database import execute_query
from backend.config import settings

router = APIRouter()

@router.get("/")
def get_visitor_count():
    query = f"""
        SELECT SUM(visitor_count) as total_visitors 
        FROM `{settings.PROJECT_ID}.{settings.DATASET}.{settings.VISITORS_TABLE}`
    """
    result = execute_query(query)
    return {"total_visitors": list(result)[0].total_visitors}

@router.post("/")
def increment_visitor_count():
    query = f"""
        INSERT INTO `{settings.PROJECT_ID}.{settings.DATASET}.{settings.VISITORS_TABLE}`
        (date, visitor_count)
        VALUES (CURRENT_DATE(), 1)
        ON DUPLICATE KEY UPDATE visitor_count = visitor_count + 1
    """
    execute_query(query)
    return {"message": "Visitor count updated"}
