from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class InspectionResponse(BaseModel):
    id: int
    device_id: int
    inspect_type: str
    overall_status: str
    result: Optional[str]
    summary: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
