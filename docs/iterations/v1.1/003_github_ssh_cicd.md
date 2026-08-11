# 003：GitHub + SSH 自动发布链路（Minimal CI/CD）

| 项目 | 内容 |
| --- | --- |
| 目标版本 | v1.1 |
| 状态 | Accepted |
| 实施分支 | `feat/cicd-iteration-003` |
| 完成日期 | 2026-08-11 |
| 生产环境 | 单台 Linux 服务器 / Docker Compose |
| 数据库迁移 | 无 |

## 1. 需求与范围（Requirements & Scope）

### 1.1 背景

此前生产发布依赖人工登录服务器、更新代码和重启服务，缺少统一的合并门禁、可重复的发布入口和明确的失败反馈。发布结果依赖操作者当时的判断，也难以证明某个生产版本已经完整通过测试、构建和健康检查。

本迭代为单台生产服务器建立一条最小可用、低维护成本的自动发布链路：Pull Request 先通过 CI；代码合并到 `main` 且该提交的 CI 成功后，GitHub Actions 通过 SSH 调用服务器上的固定脚本完成部署；部署成功后记录稳定版本，并提供经过演练的回滚入口。

### 1.2 已核实的技术基线

- 后端：FastAPI、Python 3.14、uv、Ruff、pytest。
- 前端：Next.js 16、Node.js 22、npm、ESLint、Vitest、TypeScript。
- 生产编排：Docker Compose，包含 PostgreSQL、FastAPI、Next.js 和 Caddy。
- 健康检查：`GET /api/v1/health`，同时验证应用和数据库连通性。
- 发布分支：`main`。
- 服务器项目目录：`/opt/eiheizone`。

### 1.3 交付范围

| 范围 | 结果 |
| --- | --- |
| 合并前质量门禁 | PR 必须通过后端、前端和部署产物检查 |
| 自动发布 | `main` 的 CI 成功后自动触发生产部署 |
| 单一部署入口 | Actions 只通过 SSH 执行 `/opt/eiheizone/deploy.sh` |
| 部署验证 | Compose 服务就绪且线上健康检查成功才视为发布成功 |
| 发布互斥 | 部署与回滚共享服务器文件锁，拒绝并发操作 |
| 版本追踪 | 镜像使用完整 commit SHA 标记，并记录当前及上一稳定版本 |
| 可回滚能力 | `/opt/eiheizone/rollback.sh` 可恢复上一稳定 commit 或指定 commit |
| 发布安全边界 | GitHub Secrets、Environment 和 `main` 分支保护已配置 |

### 1.4 非目标

- 不支持多机编排、灰度发布、自动流量切换或零停机发布。
- 不建设镜像仓库或独立构建产物分发链路。
- 不自动逆向执行数据库迁移。
- 不在本迭代内建设数据库和媒体文件的异机备份。

---

## 2. 核心决策（Decision Matrix）

| ID | 决策 | 结论 | 理由 |
| --- | --- | --- | --- |
| D01 | 发布触发方式 | 监听 `main` CI 的 `workflow_run` 成功事件 | 避免 push 与 CI 并行触发部署，确保部署提交已经通过完整检查 |
| D02 | 远程执行方式 | GitHub Actions + SSH | 适合单机部署，额外基础设施少，维护成本低 |
| D03 | 部署逻辑归属 | 复杂逻辑放在服务器固定脚本中 | workflow 只负责鉴权和调用，脚本可在服务器独立调试与执行 |
| D04 | 生产部署方式 | Docker Compose | 与现有生产技术栈一致，统一应用、数据库和反向代理的生命周期 |
| D05 | 版本标识 | 前后端镜像使用完整 commit SHA | 发布版本可追踪，回滚不依赖易变标签 |
| D06 | 回滚策略 | 保留当前及上一稳定版本，失败后人工确认回滚 | 避免迁移或基础设施故障触发自动反复切换 |
| D07 | SSH 主机校验 | 固定 `SSH_KNOWN_HOSTS` | 不在 workflow 中临时信任扫描结果，降低中间人攻击风险 |
| D08 | 健康判定 | Compose `--wait` + 公网 HTTP 健康检查 | 同时覆盖容器内部状态和真实访问链路 |

---

## 3. 实现契约（Implementation Contract）

### 3.1 发布链路

1. 开发分支创建 Pull Request。
2. `.github/workflows/ci.yml` 并行执行 Backend 与 Frontend 检查。
3. 两者成功后执行 Deployment artifacts 检查。
4. required checks 全部成功且分支为最新状态后，Pull Request 才可合并。
5. `main` push 的 CI 成功后，`.github/workflows/deploy.yml` 进入 `production` Environment。
6. Runner 使用固定 host key 建立 SSH 连接，仅调用 `bash /opt/eiheizone/deploy.sh`。
7. 服务器完成 fast-forward、镜像构建、Compose 更新和健康检查后记录稳定版本。

任一步返回非零退出码，当前 workflow 失败并保留日志；后续步骤不得把失败覆盖为成功。

### 3.2 CI 契约

| Job | 必须执行的检查 | 通过条件 |
| --- | --- | --- |
| Backend | PostgreSQL 17 测试服务、锁定依赖安装、Ruff、Alembic migration、pytest | lint、迁移和测试全部成功 |
| Frontend | 锁定依赖安装、ESLint、Vitest、TypeScript 类型检查、生产构建 | lint、测试、类型检查和构建全部成功 |
| Deployment artifacts | Bash 语法、Compose 配置、生产 Dockerfile 构建 | 部署脚本和生产镜像均可构建 |

CI 在 Pull Request 和 `main` push 时运行，只授予仓库内容读取权限；同一引用出现更新时，较旧的运行会被取消。

### 3.3 CD 与部署脚本契约

自动部署只接受由 `main` push 触发且结论为成功的 CI；维护者也可通过 `workflow_dispatch` 手动触发。`production` Environment 和 workflow concurrency 共同保证同一时间只有一个 Actions 部署任务。

`deploy.sh` 的职责固定为：

1. 检查必需命令、Git 仓库、生产 `.env` 和工作区状态。
2. 获取文件锁，拒绝与其他部署或回滚并发执行。
3. 获取 `origin/main`，只允许 fast-forward 更新。
4. 使用目标 commit 的完整 SHA 标记前后端镜像。
5. 执行 `docker compose up --wait` 并等待服务就绪。
6. 请求 `https://eihei.zone/api/v1/health`。
7. 成功后更新 `.deploy/` 中的当前及上一稳定 commit，并清理更早镜像。

脚本只能操作固定仓库、固定分支和固定 Compose 项目。生产业务环境变量只保存在服务器 `/opt/eiheizone/.env`，不通过 Actions 写入，也不得提交到仓库。

### 3.4 回滚契约

默认恢复上一稳定版本：

```bash
bash /opt/eiheizone/rollback.sh
```

也可指定属于 `origin/main` 历史的完整 commit SHA：

```bash
bash /opt/eiheizone/rollback.sh <40-character-commit-sha>
```

回滚优先复用带目标 SHA 标签的已验证镜像；镜像不存在时才从目标 commit 重新构建。回滚不会删除 Compose named volumes，也不会逆向执行 Alembic migration。回滚完成后仍必须通过 Compose 就绪检查和公网健康检查。

---

## 4. 配置与所有权（Configuration & Ownership）

自动发布并非只由仓库代码构成。完整链路由以下三类状态共同组成：

| 所在位置 | 交付物 | 管理方式 |
| --- | --- | --- |
| Git 仓库 | `.github/workflows/ci.yml`、`.github/workflows/deploy.yml`、`deploy.sh`、`rollback.sh`、`deploy.env.example` | 随代码评审和版本管理 |
| GitHub | `production` Environment、五项 SSH Secrets、`main` 分支保护 | 仓库管理员维护，仓库迁移后需重建 |
| 生产服务器 | `/opt/eiheizone`、`.env`、`.deploy/`、Docker volumes、部署公钥 | 服务器管理员维护，不提交到 Git |

### 4.1 GitHub Secrets

| Secret | 内容 |
| --- | --- |
| `SSH_HOST` | 生产服务器地址 |
| `SSH_PORT` | SSH 端口 |
| `SSH_USER` | 专用部署用户 |
| `SSH_PRIVATE_KEY` | 专用于部署的私钥，不复用个人私钥 |
| `SSH_KNOWN_HOSTS` | 经可信渠道核对的服务器 host key 记录 |

### 4.2 `main` 分支保护

- 禁止直接 push，所有变更必须通过 Pull Request。
- `Backend`、`Frontend`、`Deployment artifacts` 为 required checks。
- 合并前要求分支与最新 `main` 同步。
- 规则同样适用于管理员。
- 禁止强制 push 和删除分支。

### 4.3 服务器持久状态

| 路径或资源 | 用途 | Git 管理 |
| --- | --- | --- |
| `/opt/eiheizone` | 固定生产工作区 | 是，跟踪 `origin/main` |
| `/opt/eiheizone/.env` | 生产业务环境变量 | 否 |
| `/opt/eiheizone/.deploy/` | 当前及上一稳定 commit | 否，已忽略 |
| Docker named volumes | PostgreSQL 和媒体持久数据 | 否 |
| `/opt/eiheizone.manual-backup-20260811` | 自动化上线前的手工部署备份 | 否 |

---

## 5. 验收与测试（Acceptance & Testing）

| 场景 | 预期结果 | 实际证据 | 结果 |
| --- | --- | --- | --- |
| 正常 Pull Request | 三项 required checks 成功 | PR #3、PR #4 均通过 CI 后合并 | PASS |
| 故意破坏测试 | PR 不可合并 | 临时 PR #5 的 Backend 失败、Deployment artifacts 跳过，合并状态为 `BLOCKED` | PASS |
| `main` 自动部署 | CI 成功后自动进入 Deploy workflow | run `31490071913` 自动将生产更新到 `b45d2a7` | PASS |
| 服务健康检查 | Compose 服务就绪且线上接口可访问 | 部署日志成功；API 与首页均返回 HTTP 200 | PASS |
| 回滚上一稳定版本 | 恢复旧 commit 且服务健康 | `b45d2a7` 回滚到 `c949edf` 后 API 与首页返回 HTTP 200 | PASS |
| 回滚后恢复发布 | 可重新部署最新 `main` | workflow_dispatch run `31490424450` 成功恢复 `b45d2a7` | PASS |
| 健康检查失败 | Deploy workflow 返回失败 | 未在唯一生产环境主动注入故障 | NOT RUN |

健康检查失败场景未实测的原因是当前仅有唯一生产环境，主动使其失败会造成不必要的线上影响。相关非零退出分支已完成静态检查；正常部署和真实回滚路径均已实测。后续建立 staging 环境后，应补充该项故障注入测试。

---

## 6. 发布记录（Release Record）

| 时间 | 事件 | 结果 |
| --- | --- | --- |
| 2026-08-11 | PR #3 引入 CI/CD，merge commit `c949edfb620eabd0bf598e4d180394bd321a932d` | 核心链路进入 `main` |
| 2026-08-11 | PR #4 升级官方 Actions 至 v7，merge commit `b45d2a764d155cc581f7d1d079962ded0950b684` | 消除旧 Node runtime 依赖 |
| 2026-08-11 | 建立 `production` Environment、五项 SSH Secrets 和 `main` 分支保护 | GitHub 外部配置完成 |
| 2026-08-11 | 将生产目录迁移为 Git 工作区，同时保留原手工部署备份 | `.env` 和 named volumes 未进入 Git、未删除或重置 |
| 2026-08-11 | Deploy run `31488438249` attempt 4 | 首次自动部署成功 |
| 2026-08-11 | Deploy run `31490071913` | 验证合并 `main` 后无需人工登录即可更新生产 |
| 2026-08-11 | 执行 `b45d2a7` → `c949edf` → `b45d2a7` | 回滚与恢复演练成功 |

首次成功部署前的三次 attempt 均在 SSH Secret 解析阶段失败，部署脚本和容器构建尚未执行。根因是 PowerShell 写入 Secret 时的换行和编码处理，修正 Secrets 后成功建立连接。这一记录说明 SSH 凭据应以原始多行内容写入，并在 workflow 中保留解析失败的明确错误日志。

---

## 7. 风险与后续（Risks & Follow-ups）

| 风险 | 当前控制 | 后续动作 |
| --- | --- | --- |
| 数据库迁移与旧代码不兼容 | 本迭代不自动逆向迁移；要求变更保持向后兼容 | 破坏性迁移单独设计备份、双阶段发布和恢复方案 |
| 单机故障导致服务与数据同时不可用 | 代码和镜像可重建，named volumes 保留 | 建立数据库和媒体数据的异机备份及恢复演练 |
| 健康检查失败路径未在真实环境注入 | 非零分支已静态检查，成功与回滚路径已实测 | staging 可用后补充故障注入 |
| 部署用户具备 Docker 权限，权限面较大 | 使用专用 SSH key、固定目录和固定脚本入口 | 评估专用部署用户、受限 authorized_keys 或独立 runner |
| GitHub 外部配置无法随 Git 自动迁移 | 本文记录必需的 Environment、Secrets 与保护规则 | 仓库迁移清单中增加配置复核 |
| 自动化上线前的服务器备份长期占用空间 | 备份与生产目录分离，暂不自动删除 | 完成异机备份后制定保留期并人工清理 |
