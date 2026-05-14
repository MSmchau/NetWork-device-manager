from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # MySQL
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str
    # 服务
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: str = "*"
    LOG_LEVEL: str = "INFO"
    # 网络设备SSH
    DEVICE_SSH_PORT: int = 22
    DEVICE_SSH_TIMEOUT: int = 10
    BACKUP_DIR: str = "./backups"
    BACKUP_INTERVAL: int = 3600
    INSPECTION_INTERVAL: int = 3600
    STATUS_REFRESH_INTERVAL: int = 300

    class Config:
        env_file = ".env"

settings = Settings()

# 设备类型 → Netmiko device_type 映射（共享常量，避免多模块重复定义）
DEVICE_TYPE_MAP = {
    "H3C": "hp_comware",
    "华为": "huawei",
    "思科": "cisco_ios",
    "锐捷": "ruijie_os",
}
