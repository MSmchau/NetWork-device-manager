from pydantic import BaseModel
from datetime import datetime

class AlarmResponse(BaseModel):
    id: int
    device_id: int
    alarm_type: str
    level: str
    message: str
    is_handled: bool
    created_at: datetime

    class Config:
        from_attributes = True
