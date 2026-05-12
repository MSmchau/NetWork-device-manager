from app.models.database import Base, engine
from app.models.device import Device
from app.models.alarm import Alarm
from app.models.backup import BackupRecord
from app.models.inspection import InspectionRecord
from app.models.log import SystemLog

# Docker 部署时自动建表；本地迁移可用 alembic
Base.metadata.create_all(bind=engine)
