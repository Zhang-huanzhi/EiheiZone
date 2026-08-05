# Personal Family Portal V1 第五阶段测试验证报告

## 1. 文档信息

| 项目 | 内容 |
| --- | --- |
| 项目名称 | EiheiZone（Personal Family Portal） |
| 文档名称 | V1 测试验证报告 |
| 项目阶段 | V1 测试验证 |
| 文档版本 | v1.0 |
| 文档状态 | Accept |
| 创建日期 | 2026-08-01 |
| 更新日期 | 2026-08-04 |
| 维护者 | Eihei |
| 目标读者 | 项目开发者、未来维护者、作品集查看者 |
| 测试期间 | 2026-08-01 至 2026-08-03 |
| 最终回归日期 | 2026-08-03 |
| 测试范围 | V1 功能、角色权限、数据隔离、页面状态、Migration、自动化测试、覆盖率、生产构建和浏览器流程 |
| 需求基线 | `01_v1_requirements.md` v0.4 Accept |
| 设计基线 | `02_v1_design.md` v0.9 Accept |
| 任务基线 | `03_v1_plan.md` v0.4 Accept，任务 1～11 已完成 |
| 应用代码基线 | `main` / `9fa2f65a6f344e6fb3872d6b9bb5f7b2b98cd30b` |
| 测试结论 | 第五阶段通过；第六阶段已完成并在 `05_v1_release.md` 作出最终 Accept 结论 |
| 适用范围 | 本文档记录 V1 测试范围、测试证据、质量结论与遗留风险处置 |

本报告用于回答三个问题：确定版本是否满足 V1 需求、测试证据是否可追踪、遗留风险是否足以阻止进入下一阶段。它只对本文记录的版本、环境、数据和范围负责，不保证系统不存在任何未知缺陷。第五阶段的时间点事实继续保留；部署、分发、风险接受和最终发布结论以 `05_v1_release.md` 为准。

### 1.1 如何阅读本报告

| 想回答的问题 | 建议阅读位置 |
| --- | --- |
| 第五阶段是否通过、能否进入第六阶段 | §2 结论摘要、§12 最终交付判定 |
| 某一条需求是否真的测过 | §6 功能需求逐条追踪 |
| 测试执行了多少、覆盖率是多少 | §5 自动化执行与量化结果 |
| 真实用户流程和越权场景怎么验证 | §7 代表性测试用例、§8 权限矩阵验证 |
| 数据库、安全和非功能要求是否检查 | §9 数据、Migration、安全与非功能检查 |
| 还有什么风险、在第六阶段如何处置 | §10 缺陷、校正与遗留风险，及 `05_v1_release.md` |
| 怎样在本机复现主要结果 | §11 可复现命令 |

## 2. 结论摘要

### 2.1 最终结论

V1 的 Auth、Post、QA、Expenditure、Dashboard，以及 Public、Family、Owner 三类身份的核心流程均满足需求。45 条 P0 功能需求全部取得测试证据，后端权限和数据隔离、前端页面状态、生产构建、Migration 当前状态、浏览器核心流程和双视口页面检查均通过。

> **第五阶段正式测试通过，可以进入第六阶段部署发布准备。**

第五阶段结束时尚未作出生产发布决定：当时生产依赖审计有 3 个高危告警，本机没有 Docker 环境，线上部署、HTTPS 和健康检查尚未执行。第六阶段随后完成 Docker 与线上验证、PWA/TWA 分发和用户真机验收；依赖告警与异机备份经项目创建者明确接受或暂缓，最终发布状态为 Accept。

### 2.2 结果统计

| 指标 | 数量 | 结果 |
| --- | ---: | --- |
| V1 P0 功能需求 | 45 | 45 通过，0 失败，0 阻塞，0 未测试 |
| 后端自动化测试 | 229 | 229 通过 |
| 前端测试文件 | 27 | 27 通过 |
| 前端自动化测试 | 79 | 79 通过 |
| 浏览器 E2E | 2 | 2 通过 |
| 关闭的实现一致性问题 | 2 | 2 已关闭 |
| 未关闭的 V1 功能缺陷 | 0 | 无 |
| 发布前安全风险 | 1 | 生产依赖 3 个高危告警；第六阶段记录并作出风险接受决定 |
| 发布前环境限制 | 1 | 第六阶段已完成 Docker 镜像和线上运行验证 |

### 2.3 质量门禁

| 门禁 | 通过条件 | 实际结果 | 第五阶段结论 |
| --- | --- | --- | --- |
| 功能需求 | 45 条 P0 FR 均有证据且无失败 | 45/45 通过 | 通过 |
| 角色权限 | 页面入口与直接 API 调用均符合 Public/Family/Owner 权限矩阵 | 未登录返回 `401`，越权写入返回 `403` 且数据不变 | 通过 |
| 数据与隐私 | Public 不取得家庭数据；金额保持十进制精度；敏感字段不进入契约 | 自动化测试通过 | 通过 |
| 自动化回归 | 后端、前端、E2E 无失败 | 229 + 79 + 2 项通过 | 通过 |
| 静态与构建 | Ruff、TypeScript、ESLint、Next.js build 无阻断错误 | 全部通过；ESLint 仅 2 条生成目录 warning | 通过 |
| Migration | 测试库位于唯一 Alembic head，模块 Migration 测试通过 | `b73f8e21c4d6 (head)` | 通过 |
| 覆盖率 | 记录数据、范围和缺口；本项目未设硬阈值 | 后端 95%；前端行/语句 62.69% | 通过并记录改进项 |
| 生产依赖安全 | 高危告警必须修复或形成明确风险接受决定 | 3 个 high severity vulnerabilities | 第五阶段记录风险；第六阶段 Accept Risk |
| 容器与线上 | 第六阶段完成实际构建、部署和运行验证 | 第五阶段未执行；第六阶段已完成 | 通过发布验证 |

## 3. 测试对象、范围与方法

### 3.1 Git 基线

应用代码仓库为 `eiheizone/`。最终回归前后均核对以下状态：

| 项目 | 实际状态 |
| --- | --- |
| 分支 | `main` |
| 最终提交 | `9fa2f65a6f344e6fb3872d6b9bb5f7b2b98cd30b` |
| 提交说明 | `test: add coverage tooling and refresh dependencies` |
| QA 权限修正提交 | `3a46947 feat(qa): allow owner question submission` |
| 后端检查修正提交 | `2f196e3 fix: resolve backend IDE warnings` |
| 工作树 | 干净，无已跟踪或未跟踪改动 |

本报告位于应用仓库外层的项目笔记目录。因此，上表的 Git 状态只描述 `eiheizone/` 应用代码仓库，不表示本报告包含在该提交中。

### 3.2 测试范围

| 范围 | 包含内容 |
| --- | --- |
| 功能 | FR-001～FR-045；Auth、Post、QA、Expenditure、Dashboard、Public Home、Owner Workspace |
| 权限 | Public、Family、Owner 的页面访问、API 读取、API 写入和数据可见范围 |
| 数据 | UUID、UTC 时间、金额十进制字符串、QA 状态一致性、敏感字段拒绝、测试库隔离 |
| 页面 | 登录、公开页面、Family 页面、Owner 页面；加载、空数据、字段错误、无权限、Session 过期和服务错误 |
| 工程 | pytest、Vitest、Ruff、ESLint、TypeScript、Next.js build、Alembic、Playwright、覆盖率和 Git 状态 |
| 安全 | Session、签名 Double Submit CSRF、角色权限、生产依赖审计、秘密文件跟踪检查 |

### 3.3 不在第五阶段执行的范围

| 项目 | 原因 | 处理阶段 |
| --- | --- | --- |
| Docker 镜像实际构建与运行 | 本机没有 Docker CLI，未安装或启动 Docker Desktop | 第六阶段已在 VPS 完成验证 |
| 线上部署、DNS、HTTPS | 第五阶段尚未建立实际发布环境 | 第六阶段已完成验证 |
| 线上备份恢复和监控告警 | 需要真实部署资源 | 第六阶段明确异机备份暂缓并接受风险；不作为 V1 阻断项 |
| 高并发与压力测试 | V1 为家庭小规模使用，需求未设置并发指标 | 非当前验收范围；出现容量需求后补充 |
| 图片、通知、搜索、AI、多语言、用户管理 | 明确属于 V1 不做范围 | 后续版本评估 |

### 3.4 测试层级

| 层级 | 解决的问题 | 本项目证据 |
| --- | --- | --- |
| Schema/Model 单元测试 | 字段约束、枚举、金额、状态和数据库约束是否正确 | `backend/tests/*/test_*_schemas.py`、`test_*_models.py` |
| Repository/Service 测试 | 排序、分页、业务权限、事务和模块规则是否正确 | `test_*_repository.py`、`test_*_service.py` |
| API 集成测试 | Router、Session、CSRF、角色权限和 PostgreSQL 是否协同工作 | `test_*_api.py`、`test_api_permissions.py` |
| 前端组件测试 | 表单、错误、空状态、权限布局和 API Client 行为是否正确 | `frontend/src/**/*.test.ts(x)` |
| 浏览器 E2E | 用户能否从真实页面发现入口并完成核心闭环 | `frontend/e2e/core-workflows.spec.ts` |
| 静态与构建检查 | 类型、规范和生产构建是否可完成 | Ruff、ESLint、TypeScript、Next.js build |
| 覆盖率 | 哪些代码被自动化测试执行，主要缺口在哪里 | pytest-cov、Vitest V8 coverage |

覆盖率只说明代码是否被执行，不等同于需求是否正确，也不能替代权限测试和浏览器流程。因此，本报告同时保留 FR 追踪、代表性用例和覆盖率三个维度。

## 4. 环境、数据与判定规则

### 4.1 测试环境

| 项目 | 实际值 |
| --- | --- |
| 操作系统 | Windows 11 家庭中文版 25H2 |
| Python | 3.14.6 |
| pytest / pytest-cov | 9.1.1 / 7.1.0 |
| Node.js / npm | 22.16.0 / 10.9.2 |
| Next.js / React | 16.2.12 / 19.2.4 |
| 后端框架 | FastAPI、SQLAlchemy 2.x、Pydantic v2 |
| 数据库 | PostgreSQL 18.4（x86_64-windows） |
| 普通测试库 | `eiheizone_test` |
| 浏览器 | Playwright 本机 Chrome channel |
| E2E 端口 | 后端 `8100`、前端 `3100`，由 `e2e/run-local.ps1` 临时启动 |
| Docker | 本机没有可用的 Docker CLI |

### 4.2 测试数据与隔离

| 检查项 | 规则 | 实际结果 |
| --- | --- | --- |
| 账号 | 使用测试脚本随机生成的虚构 Family/Owner 账号 | 符合 |
| 密码和 Token | 不写入日志、报告、快照或 Git | 未在报告和跟踪文件中发现真实值 |
| 业务数据 | 使用带随机标识的虚构 Post、QA 和 Expenditure | 符合 |
| 数据库 | 自动化和 E2E 使用 `TEST_DATABASE_URL` | 未向开发数据库写入测试数据 |
| 测试清理 | E2E 结束后关闭临时前后端服务 | 脚本正常退出 |
| 隐私 | 不使用真实家庭信息、财务信息或身份信息 | 符合 |

### 4.3 进入标准

| 进入标准 | 状态 |
| --- | --- |
| 需求 v0.4 与架构设计 v0.9 已 Accept | 满足 |
| 第四阶段任务 1～11 已完成 | 满足 |
| 应用代码已形成明确提交 | 满足，`9fa2f65a6f34` |
| 测试库与开发库隔离 | 满足 |
| 测试账号和数据为虚构值 | 满足 |
| 前后端可以在本机启动 | 满足 |

### 4.4 结果定义与退出标准

| 结果 | 定义 |
| --- | --- |
| 通过 | 实际结果满足预期，且未出现影响该需求的未关闭缺陷 |
| 失败 | 实际结果不满足预期，或出现数据/权限错误 |
| 阻塞 | 因环境或前置条件无法执行，不能判断通过或失败 |
| 未测试 | 已纳入范围但没有执行证据 |

| 退出标准 | 实际结果 |
| --- | --- |
| 45 条 P0 功能需求均有测试证据 | 45/45 通过 |
| Public、Family、Owner 核心权限无失败 | 通过 |
| 后端、前端和核心 E2E 无失败 | 通过 |
| 无未关闭的 V1 功能阻断缺陷 | 0 个 |
| 覆盖率已生成并解释主要缺口 | 已完成 |
| 未完成的发布验证和风险已明确记录 | 已完成 |
| 正式报告已形成明确结论 | 已完成 |

## 5. 自动化执行与量化结果

### 5.1 最终回归结果

以下命令均在提交 `9fa2f65a6f34` 上于 2026-08-03 实际执行。

| 检查 | 执行方式 | 实际结果 | 耗时/补充 | 结论 |
| --- | --- | --- | --- | --- |
| 后端全量测试 | `.venv` 执行 `python -m pytest` | 229 passed | 28.07s | 通过 |
| 后端覆盖率回归 | `pytest --cov=app --cov-branch` | 229 passed，综合覆盖率 95% | 33.83s | 通过 |
| 后端静态检查 | `ruff check app tests` | All checks passed | 无错误 | 通过 |
| Migration 当前状态 | `alembic -x database=test current` | `b73f8e21c4d6 (head)` | 唯一 head | 通过 |
| 前端全量测试 | `npm test -- --run` | 27 files、79 tests passed | 15.24s | 通过 |
| 前端覆盖率回归 | `npm run test:coverage` | 27 files、79 tests passed | 19.39s | 通过 |
| TypeScript | `npm run typecheck` | 无错误 | 退出码 0 | 通过 |
| ESLint | `npm run lint` | 0 errors、2 warnings | warning 来自生成的 coverage 目录 | 通过，保留警告 |
| Next.js 生产构建 | `npm run build` | 编译、类型检查、页面数据和静态页面生成成功 | 构建退出码 0 | 通过 |
| 浏览器 E2E | `e2e/run-local.ps1` | 2 passed | 真实 Chrome；总计约 1.5 分钟 | 通过 |
| 生产依赖审计 | `npm audit --omit=dev --audit-level=high` | 3 high severity vulnerabilities | 命令退出码 1 | 第五阶段记录风险；第六阶段明确 Accept Risk |
| Git 状态 | `git status --porcelain=v1 --untracked-files=all` | 无输出 | 测试产物均被忽略 | 通过 |

后端测试直接使用现有 `.venv`，没有执行 `uv` 安装、同步或锁文件修改。

### 5.2 后端覆盖率

| 指标 | 数据 |
| --- | ---: |
| 被统计的应用语句 | 1,332 |
| 未执行语句 | 45 |
| 分支数 | 154 |
| 部分覆盖分支 | 28 |
| pytest-cov 综合覆盖率 | 95% |
| 完全覆盖而被摘要省略的文件 | 30 |

覆盖率较低的后端文件如下。这里列出缺口用于后续补测，不把数字当作功能失败。

| 文件 | 覆盖率 | 主要缺口类型 |
| --- | ---: | --- |
| `app/modules/expenditures/schemas.py` | 84% | 少数校验分支和异常分支 |
| `app/modules/auth/service.py` | 88% | 登录失败、会话处理的少数分支 |
| `app/core/security.py` | 90% | Token/签名工具的少数异常分支 |
| `app/modules/expenditures/service.py` | 90% | 不存在或越权分支 |
| `app/modules/auth/dependencies.py` | 91% | 依赖解析异常路径 |
| `app/modules/qas/service.py` | 92% | 不存在和状态边界分支 |
| `app/modules/posts/service.py` | 93% | 不存在和越权分支 |

后端 HTML 报告生成在本地 `backend/htmlcov/`，`.coverage` 和 HTML 产物不纳入 Git。

### 5.3 前端覆盖率

| 指标 | 覆盖率 |
| --- | ---: |
| Statements | 62.69% |
| Branches | 75.05% |
| Functions | 73.33% |
| Lines | 62.69% |

| 前端模块 | Statements | Branches | Functions | 解释 |
| --- | ---: | ---: | ---: | --- |
| `features/auth` | 85.46% | 84.52% | 90.47% | 登录、退出、路由和受保护布局覆盖较完整 |
| `features/dashboard` | 88.84% | 90.47% | 81.81% | 聚合展示与空状态有组件测试 |
| `features/expenditures` | 59.35% | 77.57% | 74.19% | 表单和 API 覆盖较好，展示与 Server 层不足 |
| `features/posts` | 53.61% | 82.81% | 62.96% | 表单和 API 覆盖较好，展示与 Server 层不足 |
| `features/qas` | 66.30% | 72.13% | 78.26% | 提问、回答和显示逻辑已有覆盖 |
| `features/system-status` | 78.33% | 81.25% | 100% | 加载、成功和失败状态已覆盖 |
| `lib/api` | 81.88% | 85.71% | 85.71% | 结构化错误和网络失败已覆盖 |

前端覆盖率的主要缺口是 Server Component、详情页、`loading.tsx`、`error.tsx`、`not-found.tsx` 和 `*-server.ts`。部分页面虽然在 Vitest 中显示 0%，但已由 Playwright E2E 实际访问。Vitest 覆盖率不会自动合并 Playwright 浏览器覆盖率，因此不能把 62.69%直接解释为“只有六成需求经过测试”。

本项目当前没有约定覆盖率硬阈值。建议后续优先补充权限错误页、详情页、Server 数据加载和业务展示组件，而不是为了追求数字测试简单常量或纯类型文件。

前端 HTML/LCOV 报告生成在本地 `frontend/coverage/`，不纳入 Git。

## 6. 功能需求逐条追踪

本节逐条抄录 `01_v1_requirements.md` 的 FR-001～FR-045。预期结果来自需求和架构基线；实际结果只引用本轮已执行的后端、前端或 E2E 证据。

证据简称：`BE` 为后端 pytest，`FE` 为前端 Vitest，`PERM` 为 API 权限集成测试，`E2E` 为 Playwright 核心流程，`BUILD` 为生产构建与路由清单。

### 6.1 账号与权限

| 编号 | 功能需求原文 | 预期结果 | 实际结果与证据 | 结论 |
| --- | --- | --- | --- | --- |
| FR-001 | 系统应支持项目创建者登录 | Owner 使用有效账号登录后建立 Session，并进入 `/owner` | BE Auth API 和 FE 登录表单测试通过；E2E Owner 登录后到达 `/owner` | 通过 |
| FR-002 | 系统应支持家人用户登录 | Family 使用有效账号登录后建立 Session，并进入 `/family` | BE Auth API 和 FE 登录表单测试通过；E2E Family 登录后到达 `/family` | 通过 |
| FR-003 | 系统应支持用户退出登录 | 退出后当前 Session 失效，受保护接口不再接受该 Session | BE 验证只撤销当前 Session；FE 验证退出返回公开首页和过期 Session 行为 | 通过 |
| FR-004 | 系统应能区分公开访客、家人用户和项目创建者三类身份 | 未登录为 Public；登录后 `/auth/me` 返回 Family 或 Owner；页面按角色路由 | BE 角色模型、Auth API、FE 路由和 E2E 三身份流程均通过 | 通过 |
| FR-005 | 系统应根据用户身份控制页面访问和内容访问范围 | 页面布局和后端 API 同时检查角色，隐藏按钮不能代替后端权限 | FE protected layouts 与 PERM 参数化 API 测试通过；Family 直接调用 Owner 写入 API 返回 `403` | 通过 |
| FR-006 | 未登录用户访问受保护内容时，应被阻止访问 | Public 不能取得 Family/Owner 页面内容或私有 API 数据 | E2E Public 请求 Auth、QA、Expenditure、Dashboard 私有 API 返回 `401`；受保护页面不展示私有内容 | 通过 |

### 6.2 Post 近况分享

| 编号 | 功能需求原文 | 预期结果 | 实际结果与证据 | 结论 |
| --- | --- | --- | --- | --- |
| FR-007 | 项目创建者可以创建 Post | Owner 可以提交标题、正文和可见范围，成功后返回新 Post | BE Post API、FE PostForm 与 E2E 创建公开/Family Post 均通过 | 通过 |
| FR-008 | 项目创建者可以编辑自己创建的 Post | Owner 可以修改允许字段，PATCH 只提交变化内容 | BE Service/API 与 FE PostForm 编辑测试通过；空 PATCH 不发送 | 通过 |
| FR-009 | 项目创建者可以删除 Post | Owner 删除后记录不再可读；取消确认时不删除 | BE API 删除和 FE 删除确认测试通过 | 通过 |
| FR-010 | Post 应包含标题、正文、可见范围、创建时间和更新时间 | API、Model 和 Migration 均包含必需字段，时间为带时区值 | BE Schema、Model 和 Migration 测试验证字段与时间 | 通过 |
| FR-011 | Post 应支持公开可见和仅家人可见两种可见范围 | 可见范围只接受 `public` 或 `family` | BE Schema/Model 与 FE 表单测试通过；E2E 分别创建两类 Post | 通过 |
| FR-012 | 公开访客只能查看公开可见的 Post | Public 列表和详情不能返回 Family Post | BE Repository/API/PERM 通过；E2E 公开页面看见公开 Post、看不见 Family Post | 通过 |
| FR-013 | 家人用户可以查看公开可见和仅家人可见的 Post | Family 列表包含两类可见 Post | BE 可见性查询与 E2E Family 页面均看到两类 Post | 通过 |
| FR-014 | 项目创建者可以查看和管理全部 Post | Owner 可读取两类 Post，并使用创建、编辑、删除入口 | BE 权限与 FE Owner 页面测试通过；E2E 完成创建流程 | 通过 |

### 6.3 QA 家庭问答

| 编号 | 功能需求原文 | 预期结果 | 实际结果与证据 | 结论 |
| --- | --- | --- | --- | --- |
| FR-015 | Family 和 Owner 可以提交问题 | 两类登录用户均可创建 QA；Public 不可创建 | BE QA API/Service 验证 Family、Owner 均返回 `201`；E2E 两类用户均完成提问 | 通过 |
| FR-016 | 问题应包含问题内容、提问人、创建时间和状态 | QA 响应和数据库保存 `question`、`asked_by`、`created_at`、`status` | BE Schema、Model、Migration 和 API 测试验证字段完整 | 通过 |
| FR-017 | 新提交的问题默认状态为未回答 | 创建时状态为 `unanswered`，回答内容、回答人和回答时间为空 | BE Model、Service、API 均验证完整未回答状态 | 通过 |
| FR-018 | 项目创建者可以查看 Family 和 Owner 提交的问题 | Owner 列表和详情同时显示两类提问人的 QA | BE QA API 与 E2E Owner 管理流程通过 | 通过 |
| FR-019 | 项目创建者可以回答问题 | 只有 Owner 可提交完整回答，Family 直接调用返回 `403` | BE QA API/PERM 和 FE AnswerForm 测试通过；E2E Owner 完成回答 | 通过 |
| FR-020 | 问题被回答后，状态应变更为已回答 | 同一事务写入回答、回答人、回答时间并设置 `answered` | BE Model CHECK、Service 和 API 测试通过；E2E 详情显示回答 | 通过 |
| FR-021 | Family 用户可以查看 Family 和 Owner 提交的 QA 内容 | Family 列表与详情显示两类问题及已回答内容 | BE 列表权限和 E2E Family 流程通过 | 通过 |
| FR-022 | 公开访客不能查看 QA 内容 | Public 请求 QA 列表或详情返回 `401`，公开页面不出现 QA | PERM 和 E2E Public API 检查通过 | 通过 |

### 6.4 Expenditures 重大支出记录

| 编号 | 功能需求原文 | 预期结果 | 实际结果与证据 | 结论 |
| --- | --- | --- | --- | --- |
| FR-023 | 项目创建者可以创建重大支出记录 | Owner 可以提交日期、十进制金额、币种、分类和说明 | BE API/Service、FE 表单与 E2E 创建流程通过 | 通过 |
| FR-024 | 项目创建者可以编辑重大支出记录 | Owner 可以修改允许字段；未修改字段保持不变 | BE API/Service 和 FE 差异 PATCH 测试通过 | 通过 |
| FR-025 | 项目创建者可以删除重大支出记录 | Owner 删除成功；Family 删除返回 `403`；取消确认不删除 | BE API/PERM 和 FE 删除确认测试通过 | 通过 |
| FR-026 | 支出记录应包含支出日期、金额、币种、分类和说明 | 数据库和 API 包含全部字段；金额使用十进制字符串，不经 float | BE Migration/Schema/Model 验证；`1234.5600` 原样输出为字符串 | 通过 |
| FR-027 | 家人用户可以查看重大支出记录 | Family 可以读取列表和详情，但不显示管理控件 | BE API 与 FE Family 页面测试通过；E2E Family 查看成功 | 通过 |
| FR-028 | 公开访客默认不能查看重大支出记录 | Public 列表和详情请求返回 `401`，公开页面不展示支出 | PERM 和 E2E Public API 检查通过 | 通过 |
| FR-029 | 支出记录不保存银行卡号、完整交易流水号、详细住址等敏感信息 | API 拒绝 `card_number`、`transaction_id`、`address`、附件等额外字段，表单不提供这些控件 | BE Schema/API 返回 `422`；FE 验证无敏感字段控件并显示隐私提示 | 通过 |

### 6.5 家人首页 Dashboard

| 编号 | 功能需求原文 | 预期结果 | 实际结果与证据 | 结论 |
| --- | --- | --- | --- | --- |
| FR-030 | 家人用户登录后可以访问家人首页 | Family 登录后进入 `/family` 并取得 Dashboard | FE 登录路由、Dashboard 页面与 E2E 通过 | 通过 |
| FR-031 | 家人首页应展示最近发布的 Post | Dashboard 返回固定数量的最近 Post，按权限过滤 | BE Dashboard Service/API 和 FE 页面测试通过 | 通过 |
| FR-032 | 家人首页应展示最近的 QA 内容或待回答问题 | Dashboard 返回最近 QA；Owner 额外取得待回答摘要 | BE 验证 `qas` 和 `unanswered_qas`；FE/E2E 展示通过 | 通过 |
| FR-033 | 家人首页应展示最近的重大支出记录 | Dashboard 返回最近支出摘要 | BE Dashboard API、FE 页面和 E2E 通过 | 通过 |
| FR-034 | 家人首页展示的内容应符合当前用户的权限范围 | 聚合通过各模块 Service 读取，不向 Public 返回数据 | BE Dashboard Service/PERM 通过；Public 请求返回 `401` | 通过 |

### 6.6 公开首页

| 编号 | 功能需求原文 | 预期结果 | 实际结果与证据 | 结论 |
| --- | --- | --- | --- | --- |
| FR-035 | 公开访客可以访问公开首页 | 未登录访问 `/` 成功，不要求 Session | FE Public 页面测试和 E2E 访问通过 | 通过 |
| FR-036 | 公开首页应展示项目基本介绍 | 首页存在项目名称和基本介绍内容 | E2E/页面渲染检查通过 | 通过 |
| FR-037 | 公开首页可以展示公开可见的 Post | 公开 Post 出现在首页或公开列表并可进入详情 | BE Public Post API 和 E2E 公开 Post 可见 | 通过 |
| FR-038 | 公开首页不得展示仅家人可见内容、QA 内容和重大支出记录 | 页面不请求或渲染三类私有数据；直接 API 请求也被拒绝 | BE PERM 与 E2E 同时验证页面和 API | 通过 |

### 6.7 项目创建者基础管理区

| 编号 | 功能需求原文 | 预期结果 | 实际结果与证据 | 结论 |
| --- | --- | --- | --- | --- |
| FR-039 | 项目创建者可以访问基础管理区 | Owner 登录后可访问 `/owner` | FE protected layout 与 E2E Owner 登录通过 | 通过 |
| FR-040 | 基础管理区应提供 Post 管理入口 | `/owner` 提供 Post 管理链接并可进入管理页 | FE Dashboard 页面与 E2E 导航通过 | 通过 |
| FR-041 | 基础管理区应提供 QA 管理入口 | `/owner` 提供 QA 管理和提出问题入口 | FE 页面测试通过；E2E 从工作台进入提问页并提交 | 通过 |
| FR-042 | 基础管理区应提供 Expenditures 管理入口 | `/owner` 提供 Expenditure 管理链接 | FE 页面测试与 E2E 创建支出流程通过 | 通过 |
| FR-043 | 家人用户不能访问基础管理区 | Family 访问 Owner layout 时不展示管理内容 | FE protected layout 返回 forbidden；直接 Owner API 写入返回 `403` | 通过 |
| FR-044 | 公开访客不能访问基础管理区 | Public 无法取得 Owner 页面内容或管理 API | FE protected layout/PERM/E2E 通过 | 通过 |
| FR-045 | V1 不提供用户管理页面 | 构建路由中不存在用户管理页面，Owner 工作台无用户管理入口 | Next.js build 路由清单和 Owner 页面测试均未出现用户管理功能 | 通过 |

### 6.8 FR 统计

| 模块 | FR 数量 | 通过 | 失败 | 阻塞 | 未测试 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 账号与权限 | 6 | 6 | 0 | 0 | 0 |
| Post | 8 | 8 | 0 | 0 | 0 |
| QA | 8 | 8 | 0 | 0 | 0 |
| Expenditure | 7 | 7 | 0 | 0 | 0 |
| Dashboard | 5 | 5 | 0 | 0 | 0 |
| Public Home | 4 | 4 | 0 | 0 | 0 |
| Owner Workspace | 7 | 7 | 0 | 0 | 0 |
| **合计** | **45** | **45** | **0** | **0** | **0** |

## 7. 代表性测试用例

逐条 FR 追踪用于证明需求覆盖；本节用场景用例说明用户实际怎样完成流程，以及权限失败时系统怎样响应。

| 用例 | 前置条件 | 操作摘要 | 预期结果 | 实际结果 | 结论 |
| --- | --- | --- | --- | --- | --- |
| AUTH-01 | 存在虚构 Family、Owner 账号 | 两类用户分别登录、访问所属区域并退出 | 分别进入 `/family`、`/owner`；退出后 Session 失效 | E2E 与 Auth API 均符合 | 通过 |
| AUTH-02 | 未登录 | 请求 Auth、Post 私有能力、QA、Expenditure、Dashboard API | 返回 `401`，不返回私有数据 | PERM 参数化测试和 E2E 符合 | 通过 |
| AUTH-03 | Family 已登录并取得有效 CSRF | 直接调用 Owner Post、QA 回答、Expenditure 写接口 | 返回 `403`，数据不改变 | PERM 测试符合 | 通过 |
| AUTH-04 | Session 已过期、账号停用或密码被重置 | 请求 `/api/v1/auth/me` | 返回 `401`，不继续信任旧 Session | BE Auth API 符合 | 通过 |
| POST-01 | Owner 已登录 | 创建 public 和 family 两类 Post；Public、Family 分别读取 | Public 只见公开；Family 见两类 | E2E 和 BE 可见性测试符合 | 通过 |
| POST-02 | Family 已登录，存在 Owner Post | Family 直接 PATCH/DELETE | 返回 `403`，原记录保持 | PERM/BE API 符合 | 通过 |
| QA-01 | Family 已登录 | Family 提问；Owner 回答并替换回答；Family 再读取 | 状态 `unanswered -> answered`，回答人和时间一致 | BE 与 E2E 符合 | 通过 |
| QA-02 | Owner 已登录 | 从 `/owner` 点击提出问题并提交 | 创建者为 Owner，状态 `unanswered`，详情可见 | FE 与 E2E 符合 | 通过 |
| QA-03 | Public 或 Family | Public 读取 QA；Family 尝试回答 | Public `401`；Family 回答 `403` | PERM 与 E2E 符合 | 通过 |
| EXP-01 | Owner 已登录 | 创建、编辑、删除支出；Family 读取 | CRUD 成功；Family 只读；金额精度保持 | `1234.5600` 以字符串保持，页面显示 `CNY 1,234.56` | 通过 |
| EXP-02 | Owner 已登录 | 提交 float 金额、非法币种、空修改、敏感额外字段 | 返回 `422`，不写入非法数据 | BE Schema/API 与 FE 表单符合 | 通过 |
| DASH-01 | 已存在 Post、QA、支出 | Family、Owner 请求 Dashboard | 返回最近内容；Owner 有待回答摘要；遵守权限 | BE、FE、E2E 符合 | 通过 |
| DASH-02 | 未登录 | 请求 Dashboard | 返回 `401`，不暴露聚合数据 | PERM 与 E2E 符合 | 通过 |
| UI-01 | 手机逻辑视口 | `375 x 812` 访问公共、登录和 Family 页面 | 无页面级横向溢出或明显重叠 | Playwright 检查符合 | 通过 |
| UI-02 | 桌面逻辑视口 | `1440 x 900` 访问 Owner 工作区、列表和表单 | 无页面级横向溢出或明显重叠 | Playwright 检查符合 | 通过 |
| STATE-01 | 返回空列表、字段错误、服务错误或过期 Session | 渲染对应页面或提交表单 | 空状态与错误状态区分；字段错误可定位；服务错误不泄露内部信息 | FE Dashboard、页面、表单、API Client、SystemStatus 测试符合 | 通过 |

## 8. 权限矩阵验证

| 功能/内容 | Public 预期 | Family 预期 | Owner 预期 | 实际证据 | 结论 |
| --- | --- | --- | --- | --- | --- |
| 公开首页和公开 Post | 可以 | 可以 | 可以 | Public Post API、页面测试、E2E | 通过 |
| Family Post | 不可以 | 可以 | 可以 | Post Repository/API、E2E | 通过 |
| 创建/编辑/删除 Post | 不可以 | 不可以 | 可以 | PERM、Post API、FE 表单 | 通过 |
| 查看 QA | 不可以 | 可以 | 可以 | PERM、QA API、E2E | 通过 |
| 提交 QA | 不可以 | 可以 | 可以 | QA API/Service、FE、E2E | 通过 |
| 回答 QA | 不可以 | 不可以 | 可以 | PERM、QA API、FE AnswerForm | 通过 |
| 查看 Expenditure | 不可以 | 可以 | 可以 | PERM、Expenditure API、E2E | 通过 |
| 创建/编辑/删除 Expenditure | 不可以 | 不可以 | 可以 | PERM、Expenditure API、FE | 通过 |
| Dashboard | 不可以 | 可以 | 可以 | Dashboard API、protected layouts、E2E | 通过 |
| Owner Workspace | 不可以 | 不可以 | 可以 | protected layouts、E2E | 通过 |
| 用户管理 | 不可以 | 不可以 | 不提供 | build 路由和页面检查 | 通过 |

权限测试同时检查页面和后端 API。前端隐藏管理按钮只改善使用体验；最终授权结论由 FastAPI 的依赖与 Service 决定。

## 9. 数据、Migration、安全与非功能检查

### 9.1 数据与 Migration

| 检查项 | 预期 | 实际结果 | 结论 |
| --- | --- | --- | --- |
| 数据库隔离 | 测试不写入开发库 | 使用独立 `eiheizone_test` 和 `TEST_DATABASE_URL` | 通过 |
| Alembic 状态 | 测试库处于唯一 head | `b73f8e21c4d6 (head)` | 通过 |
| 模块 Migration | Auth、Post、QA、Expenditure 表、约束和索引可由 Migration 建立 | 相关 Migration 自动化测试通过 | 通过 |
| QA 一致性 | `unanswered` 三个回答字段全空；`answered` 三字段全非空 | Model CHECK 与 Service 测试通过 | 通过 |
| 金额精度 | PostgreSQL `NUMERIC(18,4)`、Python `Decimal`、API string | Migration、Model、Schema、API 和 FE 测试通过 | 通过 |
| 时间 | 时间点以 UTC/带时区值保存 | Model 与 Schema 测试通过 | 通过 |
| 排序 | Post/QA 按创建时间倒序；支出按支出日期和创建时间倒序 | Repository 测试通过 | 通过 |

本轮没有执行会清空测试库业务表的完整 `downgrade base -> upgrade head`。已有模块 Migration 测试通过且测试库处于唯一 head；第六阶段确认生产 `upgrade head` 成功，完整降级与再升级验证转入后续维护，只能在可重建临时数据库执行。

### 9.2 安全与隐私

| 检查项 | 预期 | 实际结果 | 结论 |
| --- | --- | --- | --- |
| 密码 | Argon2id 哈希，不保存明文 | Auth Model/Service/脚本测试通过 | 通过 |
| Session | 服务端 Session；过期、停用、改密后旧 Session 失效 | Auth API 测试通过 | 通过 |
| CSRF | 签名 Double Submit；Cookie、Header、Origin 和 Session 绑定 | Security/Auth API 测试通过 | 通过 |
| 后端权限 | Public `401`，已登录越权 `403`，拒绝后数据不变 | PERM 参数化测试通过 | 通过 |
| Public 数据过滤 | Public 只取得公开 Post | Post 查询层、API 和 E2E 通过 | 通过 |
| 支出敏感字段 | 不接收或保存银行卡号、完整流水、地址、附件 | Schema/API 返回 `422`，页面无控件 | 通过 |
| Git 秘密文件 | 不跟踪真实 `.env`、`.pem`、`.key` | 跟踪列表只包含安全的 `.env.example` | 通过 |
| 生产依赖 | 高危告警得到修复或明确处置 | 当前 3 个 high severity vulnerabilities | 第六阶段记录并接受风险，不再作为 V1 阻断项 |

### 9.3 非功能需求

| 领域 | 预期 | 实际证据 | 结论 |
| --- | --- | --- | --- |
| 可维护性 | Router -> Service -> Repository，模块边界清楚 | 目录结构、模块测试、Ruff、TypeScript 通过 | 当前范围通过 |
| 可测试性 | 核心流程和权限具备自动化测试 | 229 BE、79 FE、2 E2E，覆盖率已记录 | 通过 |
| 易用性 | 家人快速看到最近信息，核心路径直接 | Dashboard、Owner Workspace、E2E 核心流程通过 | 通过 |
| 错误处理 | 加载、空数据、字段错误、无权限、Session 过期和服务失败可区分 | FE 组件与 API Client 测试通过 | 通过 |
| 响应式页面 | 手机和桌面无明显溢出或重叠 | `375 x 812`、`1440 x 900` E2E 通过 | 通过 |
| 基础性能 | 家庭小规模使用下无明显等待；不设置高并发目标 | E2E 流程正常完成，未做压力测试 | 范围内通过 |
| 可部署性 | 本地可构建运行；最终需要线上部署记录 | Next.js build 和本地 E2E 通过；第六阶段 Docker、HTTPS、健康检查和核心流程上线验证通过 | 通过 |
| 文档工程 | 需求、设计、计划、测试可互相追踪 | FR-001～FR-045 已在本报告逐条追踪 | 通过 |

## 10. 缺陷、校正与遗留风险

### 10.1 已关闭事项

| 编号 | 发现 | 影响 | 处理 | 复测 | 状态 |
| --- | --- | --- | --- | --- | --- |
| FIX-001 | QA 需求、后端权限和前端入口对 Owner 提问表述不一致 | Owner 无法通过统一入口完成需求定义中的提问能力 | 需求和设计统一为 Family/Owner 均可提问；提交 `3a46947` 补齐 Service/API 与 Owner 入口 | BE、FE、E2E 全部通过 | 已关闭 |
| FIX-002 | 后端 IDE 类型和拼写提示影响检查清晰度 | 不影响运行，但降低静态检查可信度 | 提交 `2f196e3` 修正提示 | Ruff 与 229 项后端测试通过 | 已关闭 |

本阶段未发现仍未关闭的 V1 功能缺陷。

### 10.2 遗留风险与限制

| 编号 | 类型 | 事项 | 当前证据 | 第五阶段影响 | 第六阶段要求 |
| --- | --- | --- | --- | --- | --- |
| RISK-001 | 安全 | `npm audit --omit=dev` 报告 3 个高危生产依赖告警 | Next.js 依赖的 PostCSS 与 Sharp 告警仍存在 | 不否定功能验收；第五阶段阻止直接发布 | 第六阶段已形成 V1 风险接受决定，兼容升级转入后续维护 |
| LIMIT-001 | 环境 | Docker 镜像未实际构建和运行 | 本机无 Docker CLI | 不属于第五阶段执行环境 | 在具备 Docker 的环境构建前后端镜像并验证健康检查和镜像秘密 |
| LIMIT-002 | Migration | 本轮未执行完整 `downgrade base -> upgrade head` | 模块 Migration 测试通过，当前唯一 head | 不阻止第五阶段 | 在可重建临时库验证完整迁移链 |
| COVERAGE-001 | 覆盖率 | 前端 Server Component、详情页和错误/加载页的 Vitest 覆盖不足 | 前端行/语句 62.69%，部分路径由 E2E 覆盖 | 不等同于需求未覆盖 | 优先补高风险页面和 Server 数据路径，不追求无意义百分比 |
| LIMIT-003 | 性能 | 未执行压力与并发测试 | V1 未定义并发目标，E2E 无明显等待 | 符合当前范围 | 用户规模或性能需求变化时再定义指标 |

## 11. 可复现命令

以下命令用于复现本报告的主要本地结果。执行前需要已有依赖、测试环境变量和独立 PostgreSQL 测试库。

```powershell
# backend，工作目录 eiheizone/backend
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m pytest --cov=app --cov-branch --cov-report=term-missing --cov-report=html
.\.venv\Scripts\ruff.exe check app tests
.\.venv\Scripts\alembic.exe -x database=test current

# frontend，工作目录 eiheizone/frontend
npm test -- --run
npm run test:coverage
npm run typecheck
npm run lint
npm run build
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\e2e\run-local.ps1
npm audit --omit=dev --audit-level=high
```

依赖安装、`uv sync`、Python 版本固定和锁文件同步不属于测试报告的执行步骤。不得用手工修改 `pyproject.toml` 或 `uv.lock` 代替这些操作。

## 12. 最终交付判定

| 判定项 | 结论 |
| --- | --- |
| 第五阶段是否完成 | 是 |
| V1 功能与权限是否通过正式测试 | 是，45/45 FR 通过 |
| 是否存在未关闭的 V1 功能缺陷 | 否 |
| 是否可以进入第六阶段 | 是 |
| 是否已经允许生产发布 | 是；第六阶段最终状态为 Accept |
| 当前发布阻断项 | 无；依赖告警、完整 Migration 链和异机备份已作为接受或暂缓事项记录在 `05_v1_release.md` |

- [x] 测试步骤、预期结果和实际结果已记录；
- [x] FR-001～FR-045 已逐条追踪；
- [x] 后端、前端、E2E、构建、Migration 状态和覆盖率已在最终提交上复测；
- [x] 发现的实现不一致已修正并回归；
- [x] 应用代码已提交，最终回归时工作树干净；
- [x] 未完成的发布验证和残余风险已明确记录；
- [x] 正式测试报告已完成。

**最终结论：第五阶段完成，Personal Family Portal V1 在本报告范围内测试通过。第六阶段已完成公网部署、PWA/TWA 分发和实际用户验收，并对剩余风险作出明确接受或暂缓决定；最终发布结论以 `05_v1_release.md` 为准，状态为 Accept。**
