from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.device import Device
from app.models.backup import BackupRecord
from app.services.device_service import backup_config
from app.schemas.backup import BackupRecordResponse
from app.core.response import success, paginated
from app.core.deps import common_pagination
from app.core.exceptions import BusinessError
import os

router = APIRouter()

@router.get("")
def get_backups(db: Session = Depends(get_db), pagination: dict = Depends(common_pagination)):
    total = db.query(BackupRecord).count()
    items = db.query(BackupRecord).order_by(BackupRecord.created_at.desc())\
        .offset(pagination["skip"]).limit(pagination["page_size"]).all()
    return paginated([BackupRecordResponse.model_validate(r) for r in items], total, pagination["page"], pagination["page_size"])

@router.post("/trigger/{device_id}")
def trigger_backup(device_id: int, db: Session = Depends(get_db)):
    dev = db.query(Device).filter(Device.id == device_id).first()
    if not dev:
        raise BusinessError(404, "设备不存在")
    ok, path = backup_config(dev)
    rec = BackupRecord(device_id=device_id, filename=os.path.basename(path) if path else "",
                       path=path or "", status="成功" if ok else "失败")
    db.add(rec)
    db.commit()
    return success({"success": ok, "path": path}, "备份完成" if ok else "备份失败")


@router.delete("/{record_id}")
def delete_backup(record_id: int, db: Session = Depends(get_db)):
    """删除备份记录"""
    rec = db.query(BackupRecord).filter(BackupRecord.id == record_id).first()
    if not rec:
        raise BusinessError(404, "备份记录不存在")
    # 删除物理文件
    if rec.path and os.path.exists(rec.path):
        os.remove(rec.path)
    db.delete(rec)
    db.commit()
    return success(None, "备份记录已删除")
