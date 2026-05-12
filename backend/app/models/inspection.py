from sqlalchemy import Column, Integer, String, Text, DateTime
from app.models.database import Base
import datetime

class InspectionRecord(Base):
    __tablename__ = "inspection_records"
    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, nullable=False)
    inspect_type = Column(String(32), default="standard")
    overall_status = Column(String(16), default="pending")
    result = Column(Text, nullable=True)
    summary = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.now)
