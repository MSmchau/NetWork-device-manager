from apscheduler.schedulers.background import BackgroundScheduler
from app.models.device import Device
from app.models.backup import BackupRecord
from app.models.inspection import InspectionRecord
from app.models.alarm import Alarm
from app.services.device_service import backup_config, get_device_status
from app.services.inspection_service import inspect_device
from app.models.database import SessionLocal
import datetime
import os
import json

scheduler = BackgroundScheduler()

def task_refresh_status_all():
    """定时刷新所有设备在线状态，自动生成/消除离线告警"""
    db = SessionLocal()
    try:
        devices = db.query(Device).all()
        for dev in devices:
            try:
                st = get_device_status(dev)
                dev.is_online = st["online"]
                dev.cpu_usage = st["cpu"]
                dev.mem_usage = st["mem"]
                dev.last_seen = datetime.datetime.now()

                # 自动管理离线告警
                if not st["online"]:
                    existing = db.query(Alarm).filter(
                        Alarm.device_id == dev.id,
                        Alarm.alarm_type == "offline",
                        Alarm.is_handled == False,
                    ).first()
                    if not existing:
                        db.add(Alarm(
                            device_id=dev.id,
                            alarm_type="offline",
                            level="critical",
                            message=f"设备 {dev.name}({dev.ip}) 离线",
                        ))
                else:
                    for alarm in db.query(Alarm).filter(
                        Alarm.device_id == dev.id,
                        Alarm.alarm_type == "offline",
                        Alarm.is_handled == False,
                    ).all():
                        alarm.is_handled = True
            except Exception:
                pass  # 单台设备失败不影响其他设备
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()

def task_backup_all():
    """逐台设备执行备份，每台设备独立 Session 和事务，单台失败不影响其他设备"""
    db_devices = SessionLocal()
    try:
        devices = db_devices.query(Device).all()
    finally:
        db_devices.close()
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
    db_devices = SessionLocal()
    try:
        devices = db_devices.query(Device).all()
    finally:
        db_devices.close()
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
