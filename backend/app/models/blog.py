from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class Blog(BaseModel):
    id: str
    title: str
    content: str
    tags: List[str]
    created_at: datetime = datetime.utcnow()
    updated_at: Optional[datetime]
