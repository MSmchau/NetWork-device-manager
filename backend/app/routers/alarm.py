from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.alarm import Alarm
from app.schemas.alarm import AlarmResponse
from app.core.response import paginated
from app.core.deps import common_pagination

router = APIRouter()

@router.get("/")
def get_alarms(db: Session = Depends(get_db), pagination: dict = Depends(common_pagination)):
    total = db.query(Alarm).count()
    items = db.query(Alarm).order_by(Alarm.created_at.desc())\
        .offset(pagination["skip"]).limit(pagination["page_size"]).all()
    return paginated([AlarmResponse.model_validate(r) for r in items], total, pagination["page"], pagination["page_size"])
