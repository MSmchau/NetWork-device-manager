#!/bin/bash
# NetWork-device-manager Linux 部署脚本
set -e

echo "=== 网络设备管理平台 部署开始 ==="

# 1. 环境检查
echo "[1/6] 检查环境..."
command -v python3 >/dev/null 2>&1 || { echo "需要 Python 3.10+"; exit 1; }
command -v node >/dev/null 2>&1 || { echo "需要 Node.js 18+"; exit 1; }
command -v docker >/dev/null 2>&1 && USE_DOCKER=true || USE_DOCKER=false

# 2. 后端设置
echo "[2/6] 配置后端..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt --quiet
cp .env .env.prod
sed -i 's/DEBUG=True/DEBUG=False/' .env.prod
sed -i 's/CORS_ORIGINS=\*/CORS_ORIGINS=http://localhost:3000/' .env.prod

# 3. 数据库迁移
echo "[3/6] 初始化数据库..."
# 请先手动创建 MySQL 数据库：
# mysql -u root -p -e "CREATE DATABASE network_platform DEFAULT CHARSET utf8mb4;"
# mysql -u root -p -e "CREATE USER 'net_admin'@'localhost' IDENTIFIED BY 'NetAdmin@123456';"
# mysql -u root -p -e "GRANT ALL ON network_platform.* TO 'net_admin'@'localhost';"
# mysql -u root -p -e "FLUSH PRIVILEGES;"
alembic upgrade head || echo "请先配置 MySQL 后重试"
cd ..

# 4. 前端构建
echo "[4/6] 构建前端..."
cd frontend
npm install --quiet
npm run build
cd ..

# 5. 启动服务
echo "[5/6] 启动服务..."
if [ "$USE_DOCKER" = true ]; then
    docker-compose up -d
    echo "Docker 模式启动完成"
else
    # 后台启动后端
    cd backend
    source venv/bin/activate
    nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > ../backend.log 2>&1 &
    echo "后端已启动 (PID: $!)"
    cd ..
    echo "前端构建文件在 frontend/build/"
    echo "请配置 Nginx 指向 frontend/build 并代理 /api 到 :8000"
fi

echo "=== 部署完成 ==="
echo "后端 API: http://localhost:8000/api/v1/health"
echo "API 文档: http://localhost:8000/docs"
