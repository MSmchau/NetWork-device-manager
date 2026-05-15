from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime
from app.models.database import Base
import datetime

class Device(Base):
    __tablename__ = "devices"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(64), comment="设备名")
    ip = Column(String(32), unique=True, comment="IP")
    port = Column(Integer, default=22, comment="端口")
    username = Column(String(32), comment="账号")
    password = Column(String(64), comment="密码")
    protocol = Column(String(8), default="ssh", comment="连接协议: ssh/telnet")
    device_type = Column(String(32), default="H3C")
    is_online = Column(Boolean, default=False)
    cpu_usage = Column(Float, default=0.0)
    mem_usage = Column(Float, default=0.0)
    last_seen = Column(DateTime, default=datetime.datetime.now)
    created_at = Column(DateTime, default=datetime.datetime.now)
