# EiheiZone

[English](README.md) | 简体中文 | [日本語](README.ja.md)

EiheiZone 是一个私密的家庭信息门户，用于分享生活近况、回答家人问题和记录重大支出。它在一个响应式 Web 应用中，同时提供公开内容、仅家人可见区域和 Owner 管理区。

**V1 状态：** 已于 2026 年 8 月 5 日发布并通过验收，适用于家庭小范围使用。

**生产站点：** [https://eihei.zone](https://eihei.zone)

<p align="center">
  <img src="frontend/public/screenshots/login-mobile.png" alt="EiheiZone 移动端登录页面" width="280">
</p>

> V1 应用界面使用简体中文。上方的英语、中文和日语只表示 README 文档翻译，不表示应用已经实现多语言。

## 功能

- **基于角色的访问控制：** Public、Family、Owner 使用不同区域，权限由后端强制执行。
- **Post 近况：** Owner 管理生活近况，并可选择 `public` 或 `family` 可见范围。
- **家庭问答：** Family 和 Owner 均可提问，由 Owner 回答。
- **重大支出：** 仅家庭成员可见，金额使用精确十进制，币种使用 ISO 4217 代码。
- **Dashboard：** 聚合近期 Post、QA 和 Expenditure，不建立独立 Dashboard 数据表。
- **可安装体验：** 响应式页面、PWA Manifest 和生产 HTTPS 部署。
- **运维工具：** Alembic Migration、账号维护脚本、健康检查和自动化测试。

## 角色与权限

| 能力 | Public | Family | Owner |
| --- | :---: | :---: | :---: |
| 查看公开 Post | 可以 | 可以 | 可以 |
| 查看仅家人可见 Post | 不可以 | 可以 | 可以 |
| 提交和查看家庭问题 | 不可以 | 可以 | 可以 |
| 查看重大支出 | 不可以 | 可以 | 可以 |
| 查看家庭 Dashboard | 不可以 | 可以 | 可以 |
| 管理 Post 和支出 | 不可以 | 不可以 | 可以 |
| 回答问题和使用 Owner Workspace | 不可以 | 不可以 | 可以 |

V1 不提供公开注册或用户管理页面。可信运维人员通过后端脚本创建账号和重置密码。

## 架构

```text
浏览器 / PWA
    |
    v
Caddy（HTTPS 与反向代理）
    |-- 页面请求 --> Next.js 16 / React 19
    `-- /api/* ---> FastAPI
                         |
                         v
                    PostgreSQL
```

浏览器只访问一个站点 Origin。Next.js 负责页面和交互；FastAPI 负责认证、权限、业务规则、事务和全部数据库访问。后端模块遵循 `Router -> Service -> Repository -> PostgreSQL`。

| 区域 | 技术 |
| --- | --- |
| 前端 | Next.js 16、React 19、TypeScript、Tailwind CSS 4、shadcn/ui |
| 后端 | Python 3.14、FastAPI、Pydantic 2、SQLAlchemy 2 |
| 数据 | PostgreSQL、Alembic、UUID 主键、UTC 时间、精确十进制金额 |
| 安全 | Argon2id、数据库服务端 Session、HttpOnly Cookie、签名 Double Submit CSRF |
| 测试 | pytest、Vitest、Testing Library、Playwright |
| 部署 | Docker Compose、Caddy、HTTPS、容器健康检查 |

## 项目结构

```text
eiheizone/
|-- backend/
|   |-- alembic/          # 数据库 Migration
|   |-- app/
|   |   |-- core/         # 配置、安全、错误和分页
|   |   |-- db/           # SQLAlchemy Session 与模型注册
|   |   `-- modules/      # Auth、Post、QA、Expenditure、Dashboard
|   |-- scripts/          # 账号与 E2E 准备工具
|   `-- tests/            # 后端单元测试与集成测试
|-- frontend/
|   |-- e2e/              # Playwright 核心流程
|   |-- public/           # PWA 图标与截图
|   `-- src/              # App Router 页面、组件与功能模块
|-- Caddyfile
|-- docker-compose.yml
`-- deploy.env.example
```

正式项目文档：[`docs/README.md`](docs/README.md)。V1 历史交付位于 [`docs/versions/v1/`](docs/versions/v1/)，后续变更记录在 [`docs/iterations/`](docs/iterations/)。

## 本地配置

### 环境要求

- Python 3.14 和 [`uv`](https://docs.astral.sh/uv/)
- Node.js 22 和 npm
- PostgreSQL 17 或更高版本
- PowerShell，用于执行仓库提供的 E2E 脚本

请创建相互隔离的开发库和测试库，并允许应用账号访问。示例使用 `eiheizone_dev`、`eiheizone_test` 和 `eiheizone_app`；如果本机 PostgreSQL 配置不同，请修改对应值。

以下 PowerShell 命令均从仓库根目录开始执行。

### 1. 配置后端

```powershell
cd backend
Copy-Item .env.example .env
uv sync --locked
```

继续前请编辑 `backend/.env`：

- 将 `DATABASE_URL` 和 `TEST_DATABASE_URL` 指向两个不同的数据库；
- 将 `CSRF_SECRET` 替换为至少 32 字符的随机值；
- 默认前端使用 `APP_ORIGIN=http://localhost:3000`；
- 不要提交 `backend/.env`。

升级开发库并创建首个账号：

```powershell
.\.venv\Scripts\alembic.exe upgrade head
.\.venv\Scripts\python.exe scripts\create_user.py --prompt-password
```

首个管理账号请选择 `owner` 角色。密码采用交互式输入，只应在可信终端中输入。

### 2. 配置前端

```powershell
cd ..\frontend
Copy-Item .env.example .env.local
npm ci
```

默认的 `BACKEND_API_ORIGIN=http://127.0.0.1:8000` 与下方后端命令匹配。不要覆盖已有的本地环境文件。

### 3. 启动应用

从仓库根目录分别打开两个终端。

```powershell
cd backend
.\.venv\Scripts\fastapi.exe dev app/main.py --host 127.0.0.1 --port 8000
```

```powershell
cd frontend
npm run dev
```

访问 [http://localhost:3000](http://localhost:3000)。前端把同源 `/api/*` 请求转发给 FastAPI。本地 OpenAPI 文档位于 [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)。

## 账号维护

在 `backend/` 中执行：

```powershell
# 创建 Family 或 Owner 账号
.\.venv\Scripts\python.exe scripts\create_user.py --prompt-password

# 重置密码，并使该账号的全部 Session 失效
.\.venv\Scripts\python.exe scripts\reset_password.py --prompt-password
```

生成或输入的密码不会存入仓库。初始凭证应通过私密渠道交付。

## Migration 与自动化检查

执行测试库 Migration 时，必须显式选择测试库：

```powershell
cd backend
.\.venv\Scripts\alembic.exe current
.\.venv\Scripts\alembic.exe upgrade head
.\.venv\Scripts\alembic.exe -x database=test current
.\.venv\Scripts\alembic.exe -x database=test upgrade head
```

运行后端和前端检查：

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\ruff.exe check .

cd ..\frontend
npm test
npm run lint
npm run typecheck
npm run build
```

测试库完成 Migration 后，运行浏览器核心流程：

```powershell
cd frontend
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\e2e\run-local.ps1
```

E2E 脚本只使用 `eiheizone_test`，创建虚构账号，并临时使用 `3100` 和 `8100` 端口。测试中不得使用真实家庭或财务数据。

## 生产部署

仓库中的 Compose 配置在单机上运行 PostgreSQL 17、FastAPI、Next.js 和 Caddy。`Caddyfile` 与 `docker-compose.yml` 当前按 `eihei.zone` 配置。

```powershell
Copy-Item deploy.env.example .env
# 启动前替换所有占位值，并检查域名配置。
docker compose up -d --build
docker compose ps
```

FastAPI 启动前会执行 `alembic upgrade head`。只有 Caddy 暴露宿主机端口，应用与数据库位于 Compose 内部网络。生产 `.env`、数据库备份、SSH 私钥和 Android 签名材料不得进入 Git。

## V1 边界与已知风险

- 应用界面仅有中文，且必须联网使用；不会离线缓存家庭真实数据。
- V1 不包括注册、邀请、自助找回密码、文件上传、评论、即时聊天、通知、搜索、AI 和完整记账报表。
- 生产数据保存在 Docker named volume。异机加密备份和恢复演练已暂缓，因此主机损坏可能导致永久数据丢失。
- V1 发布时接受了已知的生产依赖审计告警。扩大部署范围前应重新执行依赖审计和完整回归。
- 本仓库不包含生产秘密、真实家庭数据、Android 签名密钥或可分发 Android 安装包。
