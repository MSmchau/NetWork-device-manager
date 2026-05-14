from apscheduler.schedulers.background import BackgroundScheduler
from app.models.device import Device
from app.models.backup import BackupRecord
from app.models.inspection import InspectionRecord
from app.services.device_service import backup_config
from app.services.inspection_service import inspect_device
from app.models.database import SessionLocal
import datetime
import os
import json

scheduler = BackgroundScheduler()

def task_backup_all():
    """逐台设备执行备份，每台设备独立 Session 和事务，单台失败不影响其他设备"""
    devices = SessionLocal().query(Device).all()
    for d in devices:
        db = SessionLocal()
        try:
            ok, path = backup_config(d)
            rec = BackupRecord(
                device_id=d.id,
                filename=os.path.basename(path) if ok else "",
                path=path if ok else "",
                status="成功" if ok else "失败"
            )
            db.add(rec)
            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()

def task_inspect_all():
    """逐台设备执行巡检，每台设备独立 Session 和事务"""
    devices = SessionLocal().query(Device).all()
    for d in devices:
        db = SessionLocal()
        try:
            result = inspect_device(d)
            summary = f"{result['overall_status']} - {len(result['checks'])} 项检查"
            rec = InspectionRecord(
                device_id=d.id,
                inspect_type="standard",
                overall_status=result["overall_status"],
                result=json.dumps(result, ensure_ascii=False),
                summary=summary,
            )
            db.add(rec)
            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()
