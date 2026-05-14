from sqlalchemy import Column, String
from app.models.database import Base

class SystemSetting(Base):
    __tablename__ = "system_settings"
    key = Column(String(64), primary_key=True)
    value = Column(String(255), nullable=True)
