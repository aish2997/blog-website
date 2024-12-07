from pydantic import BaseModel
from datetime import datetime

class Comment(BaseModel):
    id: str
    blog_id: str
    commenter_name: str
    comment_text: str
    created_at: datetime = datetime.utcnow()
