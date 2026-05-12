from sqlalchemy import Column, Integer, String, DateTime
from app.models.database import Base
import datetime

class SystemLog(Base):
    __tablename__ = "system_logs"
    id = Column(Integer, primary_key=True)
    level = Column(String(16))
    content = Column(String(512))
    source = Column(String(64))
    created_at = Column(DateTime, default=datetime.datetime.now)
