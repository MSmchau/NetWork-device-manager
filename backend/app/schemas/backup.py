from pydantic import BaseModel
from datetime import datetime

class BackupRecordResponse(BaseModel):
    id: int
    device_id: int
    filename: str
    path: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
