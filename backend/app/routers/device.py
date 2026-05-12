from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.device import Device
from app.models.alarm import Alarm
from app.models.backup import BackupRecord
from app.models.inspection import InspectionRecord
from app.services.device_service import get_device_status
from app.schemas.device import DeviceCreate, DeviceUpdate
from app.core.response import success, paginated
from app.core.deps import common_pagination
from app.core.exceptions import BusinessError
import datetime

router = APIRouter()

@router.get("/")
def get_devices(db: Session = Depends(get_db), pagination: dict = Depends(common_pagination)):
    total = db.query(Device).count()
    items = db.query(Device).offset(pagination["skip"]).limit(pagination["page_size"]).all()
    return paginated(items, total, pagination["page"], pagination["page_size"])

@router.get("/{device_id}")
def get_device(device_id: int, db: Session = Depends(get_db)):
    dev = db.query(Device).filter(Device.id == device_id).first()
    if not dev:
        raise BusinessError(404, "设备不存在")
    return success(dev)

@router.post("/", status_code=201)
def create_device(data: DeviceCreate, db: Session = Depends(get_db)):
    existing = db.query(Device).filter(Device.ip == data.ip).first()
    if existing:
        raise BusinessError(400, "IP 已存在")
    dev = Device(
        name=data.name,
        ip=data.ip,
        port=data.port,
        username=data.username,
        password=data.password,
        device_type=data.device_type,
    )
    db.add(dev)
    db.commit()
    db.refresh(dev)
    return success(dev, "设备创建成功")

@router.put("/{device_id}")
def update_device(device_id: int, data: DeviceUpdate, db: Session = Depends(get_db)):
    dev = db.query(Device).filter(Device.id == device_id).first()
    if not dev:
        raise BusinessError(404, "设备不存在")
    update_data = data.model_dump(exclude_unset=True)
    if "password" in update_data and update_data["password"]:
        dev.password = update_data.pop("password")
    for field, value in update_data.items():
        setattr(dev, field, value)
    db.commit()
    db.refresh(dev)
    return success(dev, "设备已更新")

@router.delete("/{device_id}")
def delete_device(device_id: int, db: Session = Depends(get_db)):
    dev = db.query(Device).filter(Device.id == device_id).first()
    if not dev:
        raise BusinessError(404, "设备不存在")
    db.query(Alarm).filter(Alarm.device_id == device_id).delete()
    db.query(BackupRecord).filter(BackupRecord.device_id == device_id).delete()
    db.query(InspectionRecord).filter(InspectionRecord.device_id == device_id).delete()
    db.delete(dev)
    db.commit()
    return success(None, "设备已删除")

@router.post("/refresh/{device_id}")
def refresh_status(device_id: int, db: Session = Depends(get_db)):
    dev = db.query(Device).filter(Device.id == device_id).first()
    if not dev:
        raise BusinessError(404, "设备不存在")
    st = get_device_status(dev)
    dev.is_online = st["online"]
    dev.cpu_usage = st["cpu"]
    dev.mem_usage = st["mem"]
    dev.last_seen = datetime.datetime.now()
    db.commit()
    return success(st, "状态已刷新")
