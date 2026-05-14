# Docker Compose 快捷启动脚本
# 用法: .\start.ps1 [dev|build|down|logs]

switch ($args[0]) {
    "dev"   { docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d }
    "build" { docker-compose up -d --build }
    "down"  { docker-compose down }
    "logs"  { docker-compose logs -f }
    default { docker-compose up -d }
}
