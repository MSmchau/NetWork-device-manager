# 网络设备管理平台

基于 **FastAPI + React + MySQL + Docker** 的全栈网络设备运维管理平台，支持多厂商网络设备的自动巡检、配置备份、状态监控与告警管理。

## 功能特性

- **设备管理** — 添加/编辑/删除网络设备，支持 SSH 和 Telnet 双协议连接
- **批量导入/导出** — 支持 JSON 和 CSV 格式批量导入导出设备
- **自动巡检** — SSH/Telnet 采集 CPU、内存、接口状态、硬件信息、运行时长，支持 H3C/华为/思科/锐捷
- **配置备份** — 一键备份设备运行配置，支持历史记录追溯
- **状态监控** — 实时查看设备在线状态、CPU/内存使用率
- **告警管理** — 自动检测设备离线告警，支持标记已处理和删除告警
- **定时任务** — 内置调度器，支持定时全量巡检、备份和状态刷新
- **一键刷新** — 手动触发全量设备状态刷新，告警自动同步更新

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | React 18 + TypeScript + Ant Design 5 + Axios |
| 后端 | Python 3.10 + FastAPI + SQLAlchemy 2.0 + Netmiko 4 |
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
| `DEVICE_SSH_TIMEOUT` | SSH/Telnet 连接超时(秒) | `10` |
| `BACKUP_INTERVAL` | 定时备份间隔(秒) | `3600` |
| `INSPECTION_INTERVAL` | 定时巡检间隔(秒) | `3600` |
| `STATUS_REFRESH_INTERVAL` | 状态刷新间隔(秒) | `300` |
| `CORS_ORIGINS` | CORS 允许的域名 | `*` |

## 项目结构

```
netWork-device-manager/
├── backend/                  # FastAPI 后端
│   ├── app/
│   │   ├── core/            # 异常处理、日志、响应封装
│   │   ├── models/          # SQLAlchemy 数据模型
│   │   ├── routers/         # API 路由
│   │   ├── schemas/         # Pydantic 请求/响应模型
│   │   └── services/        # SSH/Telnet 连接、设备巡检、配置备份、定时调度
│   └── requirements.txt
├── frontend/                 # React 前端
│   ├── src/
│   │   ├── api/             # Axios API 封装
│   │   ├── components/      # 通用组件（设备表单、批量导入）
│   │   ├── layouts/         # 页面布局
│   │   └── pages/           # 页面（设备列表、巡检记录、告警信息）
│   └── nginx.conf           # Nginx 反向代理配置
├── docker-compose.yml        # Docker 一键部署
├── docker-compose.dev.yml    # 开发模式（热重载）
├── Makefile                  # 常用命令（dev/prod/update）
├── deploy.sh                 # Linux 部署脚本
```

## API 接口

### 设备管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/device` | 设备列表（分页） |
| POST | `/api/v1/device` | 创建设备 |
| GET | `/api/v1/device/stats` | 设备统计 |
| PUT | `/api/v1/device/{id}` | 更新设备 |
| DELETE | `/api/v1/device/{id}` | 删除设备 |
| POST | `/api/v1/device/import` | 批量导入设备 |
| GET | `/api/v1/device/export` | 批量导出设备（JSON/CSV） |
| POST | `/api/v1/device/refresh/{id}` | 刷新单台设备状态 |
| POST | `/api/v1/device/refresh-all` | 刷新所有设备状态 |

### 设备巡检

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/inspect/trigger/{id}` | 触发单台设备巡检 |
| POST | `/api/v1/inspect/trigger-all` | 触发全部设备巡检 |
| GET | `/api/v1/inspect/schedule` | 获取定时巡检配置 |
| PUT | `/api/v1/inspect/schedule` | 更新定时巡检配置 |
| GET | `/api/v1/inspect` | 巡检记录列表 |
| GET | `/api/v1/inspect/{device_id}` | 指定设备巡检记录 |
| GET | `/api/v1/inspect/report/{record_id}` | 巡检报告详情 |
| DELETE | `/api/v1/inspect/{id}` | 删除巡检记录 |

### 配置备份

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/backup/trigger/{id}` | 触发单台设备备份 |
| POST | `/api/v1/backup/trigger-all` | 触发全部设备备份 |
| GET | `/api/v1/backup` | 备份记录列表 |
| GET | `/api/v1/backup/{id}` | 备份详情 |
| GET | `/api/v1/backup/content/{id}` | 备份文件内容 |
| DELETE | `/api/v1/backup/{id}` | 删除备份记录 |

### 告警管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/alarm` | 告警列表（分页） |
| PUT | `/api/v1/alarm/{id}/handle` | 标记告警已处理 |
| DELETE | `/api/v1/alarm/{id}` | 删除告警 |

### 系统

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/health` | 健康检查 |
| GET | `/api/v1/log` | 系统日志 |

完整 API 文档在服务启动后访问 http://localhost:8000/docs。

## 支持的设备类型

| 厂商 | device_type | Netmiko 映射 | SSH | Telnet |
|------|-------------|--------------|-----|--------|
| H3C | `H3C` | `hp_comware` | ✅ | ✅ |
| 华为 | `华为` | `huawei` | ✅ | ✅ |
| 思科 | `思科` | `cisco_ios` | ✅ | ✅ |
| 锐捷 | `锐捷` | `ruijie_os` | ✅ | ✅ |

## 连接协议说明

设备支持 SSH 和 Telnet 两种连接协议，在添加或编辑设备时可选：

- **SSH**（默认）— 端口 22，安全加密连接
- **Telnet** — 端口 23，明文传输，适用于仅开放 Telnet 的老旧设备

批量导入时可通过 `protocol` 字段指定（CSV 列名或 JSON 字段），省略时默认为 SSH。

## 巡检检查项

每次巡检自动执行以下检查，按厂商执行对应命令：

| 检查项 | H3C / 华为 | 思科 | 锐捷 |
|--------|------------|------|------|
| CPU 使用率 | `display cpu-usage` | `show processes cpu` | `show cpu` |
| 内存使用率 | `display memory` | `show memory` | `show memory statistics` |
| 接口状态 | `display interface brief` | `show interfaces summary` | `show interface brief` |
| 硬件状态 | `display device` | `show inventory` | `show device` |
| 系统运行时间 | `display version` | `show version` | `show version` |

每项检查结果分为：通过(pass) / 警告(warning) / 失败(fail)。接口检查中 DOWN 端口视为空闲未用，不影响总体状态。
