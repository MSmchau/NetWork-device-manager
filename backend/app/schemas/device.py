from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class DeviceCreate(BaseModel):
    name: str = Field(..., max_length=64)
    ip: str = Field(..., max_length=32)
    port: int = Field(default=22, ge=1, le=65535)
    username: str = Field(..., max_length=32)
    password: str = Field(..., max_length=128)
    device_type: str = Field(default="H3C", max_length=32)

class DeviceUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=64)
    ip: Optional[str] = Field(None, max_length=32)
    port: Optional[int] = Field(None, ge=1, le=65535)
    username: Optional[str] = Field(None, max_length=32)
    password: Optional[str] = Field(None, max_length=128)
    device_type: Optional[str] = Field(None, max_length=32)

class DeviceResponse(BaseModel):
    id: int
    name: str
    ip: str
    port: int
    username: str
    device_type: str
    is_online: Optional[bool] = None
    cpu_usage: Optional[float] = None
    mem_usage: Optional[float] = None
    last_seen: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
