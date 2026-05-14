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
from app.services.scheduler import scheduler, task_backup_all
from app.config import settings
import os, datetime

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

@router.post("/trigger-all")
def trigger_backup_all(db: Session = Depends(get_db)):
    """手动备份全部设备"""
    devices = db.query(Device).all()
    results = []
    for dev in devices:
        ok, path = backup_config(dev)
        rec = BackupRecord(device_id=dev.id, filename=os.path.basename(path) if path else "",
                           path=path or "", status="成功" if ok else "失败")
        db.add(rec)
        results.append({"device_id": dev.id, "name": dev.name, "success": ok})
    db.commit()
    total = len(results)
    success_count = sum(1 for r in results if r["success"])
    return success({"total": total, "success": success_count, "failed": total - success_count},
                   f"全部备份完成：成功 {success_count} 台，失败 {total - success_count} 台")

@router.get("/schedule")
def get_schedule():
    """获取定时备份状态"""
    backup_job = scheduler.get_job("backup_all")
    return success({
        "enabled": backup_job is not None and scheduler.running,
        "interval": backup_job.trigger.interval_length if backup_job else settings.BACKUP_INTERVAL,
        "next_run": backup_job.next_run_time.isoformat() if backup_job and backup_job.next_run_time else None,
    })

@router.put("/schedule")
def update_schedule(data: dict):
    """更新定时备份配置"""
    interval = data.get("interval", settings.BACKUP_INTERVAL)
    enabled = data.get("enabled", True)

    # 移除旧任务
    old = scheduler.get_job("backup_all")
    if old:
        scheduler.remove_job("backup_all")

    if enabled:
        scheduler.add_job(
            task_backup_all,
            "interval",
            seconds=interval,
            id="backup_all",
            replace_existing=True,
        )
        if not scheduler.running:
            scheduler.start()

    return success({
        "enabled": enabled,
        "interval": interval,
    }, f"定时备份已{'开启' if enabled else '关闭'}，间隔 {interval} 秒")

@router.delete("/{record_id}")
def delete_backup(record_id: int, db: Session = Depends(get_db)):
    """删除备份记录"""
    rec = db.query(BackupRecord).filter(BackupRecord.id == record_id).first()
    if not rec:
        raise BusinessError(404, "备份记录不存在")
    if rec.path and os.path.exists(rec.path):
        os.remove(rec.path)
    db.delete(rec)
    db.commit()
    return success(None, "备份记录已删除")
