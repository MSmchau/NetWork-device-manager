from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.log import SystemLog
from app.core.response import paginated
from app.core.deps import common_pagination

router = APIRouter()

@router.get("/")
def get_logs(db: Session = Depends(get_db), pagination: dict = Depends(common_pagination)):
    total = db.query(SystemLog).count()
    items = db.query(SystemLog).order_by(SystemLog.created_at.desc())\
        .offset(pagination["skip"]).limit(pagination["page_size"]).all()
    return paginated(items, total, pagination["page"], pagination["page_size"])
