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
import json

router = APIRouter()

@router.post("/{device_id}")
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
