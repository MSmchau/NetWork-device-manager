from pydantic import BaseModel
from datetime import datetime

class LogResponse(BaseModel):
    id: int
    level: str
    content: str
    source: str
    created_at: datetime

    class Config:
        from_attributes = True
