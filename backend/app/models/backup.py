from sqlalchemy import Column, Integer, String, DateTime
from app.models.database import Base
import datetime

class BackupRecord(Base):
    __tablename__ = "backup_records"
    id = Column(Integer, primary_key=True)
    device_id = Column(Integer)
    filename = Column(String(255))
    path = Column(String(255))
    status = Column(String(16))
    created_at = Column(DateTime, default=datetime.datetime.now)
