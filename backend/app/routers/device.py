from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.device import Device
from app.models.alarm import Alarm
from app.models.backup import BackupRecord
from app.models.inspection import InspectionRecord
from app.services.device_service import get_device_status
from app.services.scheduler import task_refresh_status_all
from app.schemas.device import DeviceCreate, DeviceUpdate, DeviceResponse
from app.core.response import success, paginated
from app.core.deps import common_pagination
from app.core.exceptions import BusinessError
import datetime, csv, io
from typing import List
from fastapi.responses import StreamingResponse

router = APIRouter()

@router.get("")
def get_devices(db: Session = Depends(get_db), pagination: dict = Depends(common_pagination)):
    total = db.query(Device).count()
    items = db.query(Device).offset(pagination["skip"]).limit(pagination["page_size"]).all()
    return paginated([DeviceResponse.model_validate(d) for d in items], total, pagination["page"], pagination["page_size"])

@router.get("/stats")
def get_device_stats(db: Session = Depends(get_db)):
    """设备统计：总数、在线/离线、类型分布"""
    total = db.query(Device).count()
    online = db.query(Device).filter(Device.is_online == True).count()
    offline = db.query(Device).filter(Device.is_online == False).count()

    by_type_rows = db.execute(
        text("SELECT device_type, COUNT(*) AS count FROM devices GROUP BY device_type")
    ).fetchall()
    by_type = [{"name": row[0], "count": row[1]} for row in by_type_rows]

    return success({
        "total": total,
        "online": online,
        "offline": offline,
        "by_type": by_type,
    })


@router.post("/refresh-all")
def refresh_all_status():
    """立即刷新所有设备状态，并自动更新离线告警"""
    task_refresh_status_all()
    return success(None, "所有设备状态已刷新")

@router.post("/import")
def import_devices(data: List[DeviceCreate], db: Session = Depends(get_db)):
    """批量导入设备（按 IP 去重，已有 IP 自动跳过）"""
    existing_ips = {row[0] for row in db.query(Device.ip).all()}
    imported = 0
    skipped = 0

    for item in data:
        if item.ip in existing_ips:
            skipped += 1
            continue
        dev = Device(
            name=item.name, ip=item.ip, port=item.port,
            username=item.username, password=item.password,
            device_type=item.device_type,
        )
        db.add(dev)
        existing_ips.add(item.ip)
        imported += 1

    db.commit()
    return success({
        "total": len(data),
        "imported": imported,
        "skipped": skipped,
    }, f"导入完成：成功 {imported} 台，跳过 {skipped} 台")


@router.get("/export")
def export_devices(
    format: str = Query("json", pattern="^(json|csv)$"),
    db: Session = Depends(get_db),
):
    """批量导出设备（不含密码）"""
    devices = db.query(Device).all()

    if format == "csv":
        output = io.StringIO()
        output.write("﻿")  # UTF-8 BOM，解决 Excel 打开乱码
        writer = csv.writer(output)
        writer.writerow(["名称", "IP", "端口", "用户名", "设备类型", "在线", "CPU%", "内存%", "最后在线", "创建时间"])
        for d in devices:
            writer.writerow([
                d.name, d.ip, d.port, d.username, d.device_type,
                "是" if d.is_online else "否",
                d.cpu_usage or 0, d.mem_usage or 0,
                d.last_seen, d.created_at,
            ])
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv; charset=utf-8-sig",
            headers={"Content-Disposition": "attachment; filename=devices.csv"},
        )

    # JSON 格式（以文件形式下载，非 JSON API 响应）
    import json as _json
    result = [
        {
            "name": d.name, "ip": d.ip, "port": d.port,
            "username": d.username, "device_type": d.device_type,
            "is_online": d.is_online, "cpu_usage": d.cpu_usage,
            "mem_usage": d.mem_usage,
            "last_seen": d.last_seen.isoformat() if d.last_seen else None,
            "created_at": d.created_at.isoformat() if d.created_at else None,
        }
        for d in devices
    ]
    content = _json.dumps(result, ensure_ascii=False, indent=2)
    return StreamingResponse(
        iter([content]),
        media_type="application/json; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=devices.json"},
    )


@router.get("/{device_id}")
def get_device(device_id: int, db: Session = Depends(get_db)):
    dev = db.query(Device).filter(Device.id == device_id).first()
    if not dev:
        raise BusinessError(404, "设备不存在")
    return success(DeviceResponse.model_validate(dev))

@router.post("", status_code=201)
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

    # 首次创建后检测连通性，自动生成/消除离线告警
    try:
        st = get_device_status(dev)
        dev.is_online = st["online"]
        dev.cpu_usage = st["cpu"]
        dev.mem_usage = st["mem"]
        dev.last_seen = datetime.datetime.now()
        _ensure_alarm(dev, db)
        db.commit()
    except Exception:
        db.rollback()

    return success(DeviceResponse.model_validate(dev), "设备创建成功")

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
    return success(DeviceResponse.model_validate(dev), "设备已更新")

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

def _ensure_alarm(dev, db):
    """根据设备在线状态自动生成告警（去重）"""
    if not dev.is_online:
        existing = db.query(Alarm).filter(
            Alarm.device_id == dev.id,
            Alarm.alarm_type == "offline",
            Alarm.is_handled == False,
        ).first()
        if not existing:
            alarm = Alarm(
                device_id=dev.id,
                alarm_type="offline",
                level="critical",
                message=f"设备 {dev.name}({dev.ip}) 离线",
            )
            db.add(alarm)
    else:
        for alarm in db.query(Alarm).filter(
            Alarm.device_id == dev.id,
            Alarm.alarm_type == "offline",
            Alarm.is_handled == False,
        ).all():
            alarm.is_handled = True

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
    _ensure_alarm(dev, db)
    db.commit()
    return success(st, "状态已刷新")
