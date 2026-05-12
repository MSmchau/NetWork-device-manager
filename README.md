# 网络设备管理平台

基于 **FastAPI + React + MySQL + Docker** 的全栈网络设备运维管理平台，支持多厂商网络设备的自动巡检、配置备份与状态监控。

## 功能特性

- **设备管理** — 添加/编辑/删除网络设备，支持 H3C、华为、思科、锐捷
- **自动巡检** — SSH 采集 CPU、内存、接口状态、硬件信息、运行时长
- **配置备份** — 一键备份设备运行配置，支持历史记录追溯
- **状态监控** — 实时查看设备在线状态、CPU/内存使用率
- **告警管理** — 统一查看设备告警信息
- **定时任务** — 内置调度器，支持定时全量备份

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | React 18 + TypeScript + Ant Design 5 + Axios |
| 后端 | Python 3.10 + FastAPI + SQLAlchemy 2.0 + Netmiko |
| 数据库 | MySQL 8.0 |
| 部署 | Docker Compose / 手动部署 |

## 快速启动（Docker）

```bash
# 克隆仓库
git clone https://github.com/MSmchau/NetWork-device-manager.git
cd NetWork-device-manager

# 启动所有服务
docker compose up -d

# 查看日志
docker compose logs -f backend
```

访问 http://localhost:3000 进入前端界面。

## 开发模式（热重载，推荐日常使用）

修改代码后无需重建镜像，改动即时生效：

```bash
# 首次启动开发模式
make dev
# 或: docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# 拉取代码后快速更新（仅后端变更是秒级重启）
make update

# 查看日志
docker compose logs -f backend
```

原理：
- **后端**：挂载本地源码到容器，`uvicorn --reload` 检测文件变更自动重启
- **前端**：`npm start` 开发服务器，浏览器 HMR 热更新模块
- 只有 `requirements.txt` 或 `package.json` 变更时才需 `make dev` 重建

## 手动部署

```bash
# 1. 创建 MySQL 数据库
mysql -u root -p -e "CREATE DATABASE network_platform DEFAULT CHARSET utf8mb4;"
mysql -u root -p -e "CREATE USER 'net_admin'@'localhost' IDENTIFIED BY 'NetAdmin@123456';"
mysql -u root -p -e "GRANT ALL ON network_platform.* TO 'net_admin'@'localhost';"
mysql -u root -p -e "FLUSH PRIVILEGES;"

# 2. 配置后端
cd backend
cp .env .env.prod
# 修改 .env.prod 中的数据库配置
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. 启动后端
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 4. 构建并启动前端
cd frontend
npm install
npm run build
# 将 build/ 目录部署到 Nginx，代理 /api 到 :8000
```

## 环境变量

后端配置通过 `backend/.env` 文件管理：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DB_HOST` | 数据库地址 | `127.0.0.1` |
| `DB_PORT` | 数据库端口 | `3306` |
| `DB_USER` | 数据库用户 | `net_admin` |
| `DB_PASSWORD` | 数据库密码 | `NetAdmin@123456` |
| `DB_NAME` | 数据库名 | `network_platform` |
| `FERNET_SECRET_KEY` | Fernet 加密密钥 | — |
| `JWT_SECRET_KEY` | JWT 签名密钥 | — |
| `DEVICE_SSH_PORT` | 设备 SSH 端口 | `22` |
| `DEVICE_SSH_TIMEOUT` | SSH 连接超时(秒) | `10` |
| `BACKUP_INTERVAL` | 定时备份间隔(秒) | `3600` |

## 项目结构

```
netWork-device-manager/
├── backend/                  # FastAPI 后端
│   ├── app/
│   │   ├── core/            # 异常处理、日志、响应封装
│   │   ├── models/          # SQLAlchemy 数据模型
│   │   ├── routers/         # API 路由
│   │   ├── schemas/         # Pydantic 请求/响应模型
│   │   └── services/        # SSH 连接、设备巡检、配置备份
│   └── requirements.txt
├── frontend/                 # React 前端
│   ├── src/
│   │   ├── api/             # Axios API 封装
│   │   ├── components/      # 通用组件（设备表单）
│   │   ├── layouts/         # 页面布局
│   │   └── pages/           # 页面（设备列表、巡检记录）
│   └── nginx.conf           # Nginx 反向代理配置
├── docker-compose.yml        # Docker 一键部署
├── docker-compose.dev.yml    # 开发模式（热重载）
├── Makefile                  # 常用命令（dev/prod/update）
├── deploy.sh                 # Linux 部署脚本
```

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/health` | 健康检查 |
| GET/POST | `/api/v1/device` | 设备列表/创建设备 |
| GET/PUT/DELETE | `/api/v1/device/{id}` | 设备详情/更新/删除 |
| POST | `/api/v1/device/refresh/{id}` | 刷新设备状态 |
| POST | `/api/v1/inspect/{id}` | 触发设备巡检 |
| GET | `/api/v1/inspect/{id}` | 巡检历史记录 |
| GET | `/api/v1/inspect/report/{id}` | 巡检报告详情 |
| POST | `/api/v1/backup/trigger/{id}` | 触发配置备份 |
| GET | `/api/v1/backup` | 备份记录列表 |
| GET | `/api/v1/alarm` | 告警记录列表 |

完整 API 文档在服务启动后访问 http://localhost:8000/docs。

## 支持的设备类型

| 厂商 | device_type | Netmiko 映射 |
|------|-------------|--------------|
| H3C | `H3C` | `hp_comware` |
| 华为 | `华为` | `huawei` |
| 思科 | `思科` | `cisco_ios` |
| 锐捷 | `锐捷` | `ruijie_os` |
