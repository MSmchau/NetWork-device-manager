from sqlalchemy import Column, Integer, String, Boolean, DateTime
from app.models.database import Base
import datetime

class Alarm(Base):
    __tablename__ = "alarms"
    id = Column(Integer, primary_key=True)
    device_id = Column(Integer)
    alarm_type = Column(String(32))
    level = Column(String(16))
    message = Column(String(255))
    is_handled = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.now)
