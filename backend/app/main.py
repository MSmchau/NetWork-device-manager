from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import setup_logging
from app.routers import device, alarm, backup, log, inspection, health
from app.services.scheduler import scheduler, task_backup_all, task_inspect_all
from app.models import inspection as inspection_model

app = FastAPI(title="网络设备管理平台")
app.router.redirect_slashes = False  # 禁止尾斜杠自动重定向（避免 307 到 Docker 内部域名）

# CORS（生产环境应将 * 替换为具体域名）
origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册全局异常处理器
register_exception_handlers(app)

# 注册路由（使用可配置的 API 版本前缀）
P = settings.API_V1_PREFIX
app.include_router(health.router, prefix=P, tags=["系统"])
app.include_router(device.router, prefix=f"{P}/device", tags=["设备"])
app.include_router(alarm.router, prefix=f"{P}/alarm", tags=["告警"])
app.include_router(backup.router, prefix=f"{P}/backup", tags=["备份"])
app.include_router(log.router, prefix=f"{P}/log", tags=["日志"])
app.include_router(inspection.router, prefix=f"{P}/inspect", tags=["巡检"])

@app.on_event("startup")
def on_startup():
    setup_logging()
    scheduler.add_job(
        task_backup_all,
        "interval",
        seconds=settings.BACKUP_INTERVAL,
        id="backup_all",
    )
    scheduler.add_job(
        task_inspect_all,
        "interval",
        seconds=settings.INSPECTION_INTERVAL,
        id="inspect_all",
    )
    scheduler.start()

@app.on_event("shutdown")
def on_shutdown():
    scheduler.shutdown()
