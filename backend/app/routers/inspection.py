from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.device import Device
from app.models.inspection import InspectionRecord
from app.services.inspection_service import inspect_device
from app.schemas.inspection import InspectionResponse
from app.core.response import success, paginated
from app.core.deps import common_pagination
from app.core.exceptions import BusinessError
from app.services.scheduler import scheduler, task_inspect_all
from app.config import settings
from app.models.setting import SystemSetting
import json

router = APIRouter()

@router.post("/trigger/{device_id}")
def trigger_inspection(device_id: int, db: Session = Depends(get_db)):
    dev = db.query(Device).filter(Device.id == device_id).first()
    if not dev:
        raise BusinessError(404, "设备不存在")
    result = inspect_device(dev)
    summary = f"{result['overall_status']} - {len(result['checks'])} 项检查"
    record = InspectionRecord(
        device_id=device_id,
        inspect_type="standard",
        overall_status=result["overall_status"],
        result=json.dumps(result, ensure_ascii=False),
        summary=summary,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return success({"id": record.id, "overall_status": result["overall_status"], "summary": summary}, "巡检完成")

@router.post("/trigger-all")
def trigger_inspection_all(db: Session = Depends(get_db)):
    """手动巡检全部设备"""
    devices = db.query(Device).all()
    results = []
    for dev in devices:
        try:
            result = inspect_device(dev)
            summary = f"{result['overall_status']} - {len(result['checks'])} 项检查"
            record = InspectionRecord(
                device_id=dev.id,
                inspect_type="standard",
                overall_status=result["overall_status"],
                result=json.dumps(result, ensure_ascii=False),
                summary=summary,
            )
            db.add(record)
            results.append({"device_id": dev.id, "name": dev.name, "status": result["overall_status"]})
        except Exception:
            results.append({"device_id": dev.id, "name": dev.name, "status": "failed"})
    db.commit()
    total = len(results)
    success_count = sum(1 for r in results if r["status"] in ("healthy", "warning"))
    return success({"total": total, "success": success_count, "failed": total - success_count},
                   f"全部巡检完成：成功 {success_count} 台，失败 {total - success_count} 台")

@router.get("/schedule")
def get_schedule():
    """获取定时巡检状态"""
    job = scheduler.get_job("inspect_all")
    return success({
        "enabled": job is not None and scheduler.running,
        "interval": job.trigger.interval_length if job else settings.INSPECTION_INTERVAL,
        "next_run": job.next_run_time.isoformat() if job and job.next_run_time else None,
    })

@router.put("/schedule")
def update_schedule(data: dict, db: Session = Depends(get_db)):
    """更新定时巡检配置"""
    interval = data.get("interval", settings.INSPECTION_INTERVAL)
    enabled = data.get("enabled", True)

    # 持久化开关状态
    for key, val in [("inspect_all_enabled", str(enabled).lower()),
                     ("inspect_all_interval", str(interval))]:
        row = db.query(SystemSetting).filter(SystemSetting.key == key).first()
        if row:
            row.value = val
        else:
            db.add(SystemSetting(key=key, value=val))
    db.commit()

    old = scheduler.get_job("inspect_all")
    if old:
        scheduler.remove_job("inspect_all")

    if enabled:
        scheduler.add_job(
            task_inspect_all,
            "interval",
            seconds=interval,
            id="inspect_all",
            replace_existing=True,
        )
        if not scheduler.running:
            scheduler.start()

    return success({
        "enabled": enabled,
        "interval": interval,
    }, f"定时巡检已{'开启' if enabled else '关闭'}，间隔 {interval} 秒")

@router.get("/{device_id}")
def get_inspection_history(device_id: int, db: Session = Depends(get_db), pagination: dict = Depends(common_pagination)):
    total = db.query(InspectionRecord).filter(InspectionRecord.device_id == device_id).count()
    items = db.query(InspectionRecord).filter(InspectionRecord.device_id == device_id)\
        .order_by(InspectionRecord.created_at.desc())\
        .offset(pagination["skip"]).limit(pagination["page_size"]).all()
    return paginated([InspectionResponse.model_validate(r) for r in items], total, pagination["page"], pagination["page_size"])

@router.get("/report/{record_id}")
def get_inspection_report(record_id: int, db: Session = Depends(get_db)):
    record = db.query(InspectionRecord).filter(InspectionRecord.id == record_id).first()
    if not record:
        raise BusinessError(404, "巡检记录不存在")
    return success({
        "id": record.id,
        "device_id": record.device_id,
        "inspect_type": record.inspect_type,
        "overall_status": record.overall_status,
        "result": json.loads(record.result) if record.result else None,
        "summary": record.summary,
        "created_at": record.created_at,
    })

@router.delete("/{record_id}")
def delete_inspection(record_id: int, db: Session = Depends(get_db)):
    """删除巡检记录"""
    rec = db.query(InspectionRecord).filter(InspectionRecord.id == record_id).first()
    if not rec:
        raise BusinessError(404, "巡检记录不存在")
    db.delete(rec)
    db.commit()
    return success(None, "巡检记录已删除")
