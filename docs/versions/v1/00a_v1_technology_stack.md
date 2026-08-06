# EiheiZone V1 技术栈

## 1. 文档信息

| 项目 | 内容 |
| --- | --- |
| 项目名称 | EiheiZone（Personal Family Portal） |
| 文档名称 | V1 技术栈与运行基线 |
| 文档版本 | v1.0 |
| 文档状态 | Accept |
| 基线日期 | 2026-08-05 |
| 维护者 | Eihei |
| 目标读者 | 项目开发者、未来维护者、作品集查看者 |
| 适用范围 | V1 开发、测试、部署和客户端分发使用的最终技术选择 |

## 2. 文档目的

本文档回答“EiheiZone V1 最终由哪些技术组成，各自负责什么”。它记录已经落地并通过验收的技术基线，不展开候选方案比较和个人开发复盘。

## 3. 最终技术栈

| 区域 | 最终选择 | 主要职责 |
| --- | --- | --- |
| 前端运行时 | Node.js 22、npm | 前端依赖、开发服务器和生产构建 |
| Web 框架 | Next.js 16、React 19 | App Router 页面、服务端渲染和交互 |
| 前端语言 | TypeScript strict | 类型检查与前端实现 |
| 样式与组件 | Tailwind CSS 4、shadcn/ui、lucide-react | 响应式界面、基础组件和图标 |
| 后端运行时 | Python 3.14、uv | 后端运行、依赖锁定和虚拟环境 |
| API 框架 | FastAPI | HTTP API、依赖注入和 OpenAPI |
| 数据校验 | Pydantic 2、pydantic-settings | API Schema 与环境配置校验 |
| ORM | SQLAlchemy 2 | Model、查询、Session 和事务协作 |
| 数据库驱动 | psycopg 3 | Python 与 PostgreSQL 通信 |
| 数据库 | PostgreSQL 17 | 用户、Session 和全部业务数据 |
| Schema 迁移 | Alembic | 数据库结构版本管理与升级 |
| 密码安全 | pwdlib、Argon2id | 密码哈希与校验 |
| 后端测试 | Pytest、HTTPX、pytest-cov | 单元、集成、API、Migration 和覆盖率测试 |
| 前端测试 | Vitest、Testing Library、jsdom | 组件、交互和 API 客户端测试 |
| 浏览器测试 | Playwright | 三类角色、权限边界和核心工作流 |
| 静态检查 | Ruff、ESLint、TypeScript | Python Lint、前端 Lint 与类型检查 |
| 容器与编排 | Docker、Docker Compose | 生产镜像与四服务编排 |
| 入口网关 | Caddy | HTTPS、证书续期、跳转和反向代理 |
| 云端运行 | 腾讯云首尔 Linux VPS | 单机生产运行环境 |
| Web 安装 | PWA Manifest | 浏览器安装入口，不提供离线数据能力 |
| Android 分发 | PWABuilder、Android SDK、WebView APK | TWA 打包与目标设备兼容性兜底 |

依赖的准确可安装版本以 `backend/uv.lock` 和 `frontend/package-lock.json` 为准；本文档只固定 V1 的主要版本和职责边界。

## 4. 系统职责与拓扑
![[Pasted image 20260805193425.png]]

- Next.js 负责页面、路由、表单和交互，不直接访问数据库；
- FastAPI 负责认证、授权、业务规则、事务和全部数据库访问；
- PostgreSQL 保存业务数据与服务端 Session，仅在 Compose 内部网络中访问；
- 浏览器只使用一个站点 Origin，普通路径进入 Next.js，`/api/*` 进入 FastAPI；
- 后端采用模块化单体，业务模块内部遵循 `Router -> Service -> Repository`；
- Caddy 是唯一对公网暴露 `80/443` 的服务。

## 5. 安全与数据基线

| 领域 | V1 基线 |
| --- | --- |
| 登录状态 | PostgreSQL 服务端 Session，30 天固定有效期 |
| 浏览器凭证 | Secure、HttpOnly、SameSite Cookie |
| CSRF | 签名 Double Submit Cookie，修改请求必须校验 Token |
| 授权 | Router 入口检查，Service 最终校验，Repository 带条件查询 |
| 密码 | Argon2id 哈希，不保存明文 |
| 主键 | UUID |
| 时间 | 数据库存 UTC，界面按配置时区显示 |
| 金额 | PostgreSQL `NUMERIC(18,4)`，币种使用 ISO 4217 代码 |
| 状态 | 应用枚举与数据库 CHECK 约束 |
| 生产秘密 | 保存在 VPS 受限环境文件中，不进入 Git、镜像或正式文档 |

## 6. 开发、测试与生产环境

| 环境 | 运行方式 | 数据边界 |
| --- | --- | --- |
| 本地开发 | Next.js、FastAPI 和本机 PostgreSQL 分别运行 | 使用独立开发库 |
| 自动化测试 | Pytest、Vitest、Playwright；E2E 临时使用 `3100/8100` | 只使用独立测试库和虚构数据 |
| 生产 | VPS 上由 Docker Compose 运行 PostgreSQL、FastAPI、Next.js、Caddy | 真实数据只保存在生产数据库 |

本地配置从 `.env.example` 创建但不提交；生产配置从 `deploy.env.example` 确认变量名称后在 VPS 单独维护。应用代码、环境配置和数据不得混用。

## 7. 发布与运维边界

- 本地完成测试、Lint、类型检查和生产构建后，通过 SSH/SCP 上传源码；
- VPS 使用 Docker Compose 构建、启动并检查四个服务；
- FastAPI 容器启动前执行 `alembic upgrade head`；
- PostgreSQL 使用 Docker named volume 持久化；
- Web 先发布，PWA 随 Web 提供，Android 包最后进行真机验证；
- V1 使用手工发布，不启用 CI/CD、镜像仓库或 Terraform；
- 普通 DNS 直接指向 VPS，V1 不使用 Cloudflare 代理。

## 8. V1 未纳入的技术

以下能力没有足够的 V1 需求支撑，因此不属于当前技术基线：

- 微服务、Redis、消息队列和独立 Worker；
- pgvector、全文检索和 AI 基础设施；
- 文件对象存储和上传链路；
- Cloudflare/CDN、负载均衡、多实例和 Kubernetes；
- 托管 PostgreSQL、高可用数据库和异机自动备份；
- CI/CD、镜像仓库和 Terraform 等 IaC；
- 原生 Android 业务客户端和离线家庭数据缓存。

这些技术不是被永久否定；只有用户量、数据价值、协作方式、发布频率或可靠性要求发生变化时，才进入新一轮评估。

## 9. 验收状态与已知风险

V1 技术栈已完成本地自动化测试、生产构建、Docker 运行、HTTPS、线上核心流程、PWA、Android 真机和 VPS 重启恢复验证，最终发布状态为 **Accept**。

当前仍保留三类已知事项：生产依赖审计存在 3 个 high severity 告警；完整 Migration 降级再升级留待临时数据库验证；异机备份与恢复演练尚未建设。它们已在 `05_v1_release.md` 中标记为 Accept Risk 或 Deferred，不应被表述为已完成能力。
