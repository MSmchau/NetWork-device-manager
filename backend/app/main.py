from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import setup_logging
from app.routers import device, alarm, backup, log, inspection, health
from app.services.scheduler import scheduler, task_backup_all, task_inspect_all
from app.models import inspection as inspection_model
from app.models.setting import SystemSetting
from app.models.device import Device as DeviceModel
from app.models.alarm import Alarm as AlarmModel
from app.models.database import SessionLocal

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

    def _init_offline_alarms():
        """启动时扫描所有离线设备，补全缺失的离线告警"""
        db = SessionLocal()
        try:
            offline_devices = db.query(DeviceModel).filter(DeviceModel.is_online == False).all()
            for dev in offline_devices:
                existing = db.query(AlarmModel).filter(
                    AlarmModel.device_id == dev.id,
                    AlarmModel.alarm_type == "offline",
                    AlarmModel.is_handled == False,
                ).first()
                if not existing:
                    db.add(AlarmModel(
                        device_id=dev.id,
                        alarm_type="offline",
                        level="critical",
                        message=f"设备 {dev.name}({dev.ip}) 离线",
                    ))
            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()

    _init_offline_alarms()

    def _load_schedule(job_id, task, default_interval):
        """从 DB 读取定时开关状态，按需注册任务"""
        db = SessionLocal()
        try:
            enabled_str = db.query(SystemSetting).filter(SystemSetting.key == f"{job_id}_enabled").first()
            interval_str = db.query(SystemSetting).filter(SystemSetting.key == f"{job_id}_interval").first()
            enabled = enabled_str.value == "true" if enabled_str else True
            interval = int(interval_str.value) if interval_str else default_interval
            if enabled:
                scheduler.add_job(task, "interval", seconds=interval, id=job_id)
        except Exception:
            scheduler.add_job(task, "interval", seconds=default_interval, id=job_id)
        finally:
            db.close()

    _load_schedule("backup_all", task_backup_all, settings.BACKUP_INTERVAL)
    _load_schedule("inspect_all", task_inspect_all, settings.INSPECTION_INTERVAL)
    scheduler.start()

@app.on_event("shutdown")
def on_shutdown():
    scheduler.shutdown()
