from fastapi import APIRouter
from sqlalchemy import text
from app.core.response import success
from app.services.scheduler import scheduler
from app.models.database import get_db

router = APIRouter(tags=["系统"])

@router.get("/health")
def health_check():
    """健康检查：验证服务、数据库、定时任务的运行状态"""
    db_ok = False
    db_gen = None
    try:
        db_gen = get_db()
        db = next(db_gen)
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        pass
    finally:
        if db_gen is not None:
            db_gen.close()
    return success({
        "status": "running",
        "database": "connected" if db_ok else "disconnected",
        "scheduler": "running" if scheduler and scheduler.running else "stopped",
    })
