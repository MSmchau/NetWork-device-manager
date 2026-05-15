from fastapi import APIRouter
from sqlalchemy import text
from app.core.response import success
from app.services.scheduler import scheduler
from app.models.database import SessionLocal

router = APIRouter(tags=["系统"])

@router.get("/health")
def health_check():
    """健康检查：验证服务、数据库、定时任务的运行状态"""
    db_ok = False
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db_ok = True
        db.close()
    except Exception:
        pass
    return success({
        "status": "running",
        "database": "connected" if db_ok else "disconnected",
        "scheduler": "running" if scheduler and scheduler.running else "stopped",
    })
