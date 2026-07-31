# EiheiZone

[English](README.md) | 简体中文 | [日本語](README.ja.md)

EiheiZone 是一个家庭信息应用。前端使用 Next.js，后端使用 FastAPI，全部数据由后端访问本机 PostgreSQL。

## 环境要求

- Python 3.14 与 `uv`
- Node.js 20.9 或更高版本与 npm
- 本机 PostgreSQL，沿用已有 `eiheizone_dev`、`eiheizone_test` 和 `eiheizone_app`
- Docker 仅用于可选的前后端镜像构建，不运行 PostgreSQL

## 首次准备

后端：

```powershell
cd backend
Copy-Item .env.example .env
# 按本机现有数据库配置修改 .env，并为 CSRF_SECRET 设置至少 32 位的本地随机值
uv sync --locked
.\.venv\Scripts\alembic.exe upgrade head
.\.venv\Scripts\python.exe scripts\create_user.py --prompt-password
```

`create_user.py` 会交互式询问登录名、显示名和 `family`/`owner` 角色。密码只在终端输入，不要写入仓库。

前端：

```powershell
cd ..\frontend
Copy-Item .env.example .env.local
npm ci
```

已有本地环境不要覆盖现有 `.env` 或 `.env.local`。

## 本地启动

分别打开两个终端。

```powershell
cd backend
.\.venv\Scripts\fastapi.exe dev app/main.py --host 127.0.0.1 --port 8000
```

```powershell
cd frontend
npm run dev
```

浏览器访问 `http://localhost:3000`。前端通过同源 `/api` 转发到 `BACKEND_API_ORIGIN`，后端 `APP_ORIGIN` 应与浏览器访问的 Origin 一致。

## 数据库迁移与检查

开发库迁移：

```powershell
cd backend
.\.venv\Scripts\alembic.exe current
.\.venv\Scripts\alembic.exe upgrade head
```

测试库必须通过 `-x database=test` 明确选择：

```powershell
.\.venv\Scripts\alembic.exe -x database=test current
.\.venv\Scripts\alembic.exe -x database=test upgrade head
```

自动检查：

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\ruff.exe check .

cd ..\frontend
npm run lint
npm run typecheck
npm test
npm run build
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\e2e\run-local.ps1
```

E2E 脚本只连接 `eiheizone_test`，创建虚构账号，并仅将 `3100`、`8100` 端口用于本轮启动的进程。不要把真实家庭信息用于测试。

## 可选：Docker 镜像

PostgreSQL 保持在宿主机。前端 API 地址在构建时写入 Next.js rewrites：

```powershell
docker build -t eiheizone-backend:v1 .\backend
docker build --build-arg BACKEND_API_ORIGIN=http://host.docker.internal:8000 -t eiheizone-frontend:v1 .\frontend
```

镜像运行时必须通过环境变量提供本机实际配置，不能把 `.env` 或密码复制进镜像。后端容器访问宿主机 PostgreSQL 时，`DATABASE_URL` 的主机应使用 `host.docker.internal`；浏览器仍通过 `http://localhost:3000` 访问前端。
