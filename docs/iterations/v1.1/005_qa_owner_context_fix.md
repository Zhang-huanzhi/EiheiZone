# 005：Owner QA 提问路由上下文修复（Owner QA Route Context Fix）

| 项目 | 内容 |
| --- | --- |
| 目标版本 | v1.1.0 |
| 状态 | Accepted |
| 类型 | fix |
| 分支 | 由开发者创建的 QA 路由修复分支 |
| 完成日期 | 2026-08-13 |
| 数据库迁移 | 无 |

## 1. 需求与范围（Requirements & Scope）

Owner 登录后从 `/owner` 或 `/owner/qas` 发起提问，原流程会进入 Family 提问页。提交成功后又固定跳转到 Family QA 详情页，导致 Owner 离开管理区域；Family 导航中没有返回 Owner 工作台的入口，用户只能手动修改 URL。

本次修复保证 QA 提问流程保留发起方的区域上下文：

- Owner 从管理区域进入 `/owner/qas/new`；
- Owner 提交成功后进入 `/owner/qas/:qaId`，可直接查看问题并进行回答；
- Owner 提问页的“返回问答管理”和“取消”均返回 `/owner/qas`；
- Family 原有流程保持 `/family/qas/new` -> `/family/qas/:qaId`；
- 未登录提交时，登录回跳路径与当前区域保持一致。

本次不增加跨区域切换导航，不修改 QA 业务规则、后端 API、权限模型、数据库结构或部署方式。

## 2. 根因分析（Root Cause）

问题由前端路由目标写死造成，而不是认证或会话失效：

1. Owner 工作台和 Owner 问答管理页的“提出问题”链接都指向 `/family/qas/new`。
2. 共享 `QuestionForm` 的成功跳转固定为 `/family/qas/:qaId`。
3. Family 提问页的返回和取消链接固定为 `/family/qas`。
4. Owner 仍然保持登录，但页面已挂载 Family layout，只呈现 Family 主导航，因此没有可见的 Owner 返回路径。

## 3. 技术方案与决策（Design & Decisions）

### 3.1 路由契约

| 用户入口 | 提问页 | 提交成功 | 返回 / 取消 |
| --- | --- | --- | --- |
| Family 问答列表 | `/family/qas/new` | `/family/qas/:qaId` | `/family/qas` |
| Owner 工作台 | `/owner/qas/new` | `/owner/qas/:qaId` | `/owner/qas` |
| Owner 问答管理 | `/owner/qas/new` | `/owner/qas/:qaId` | `/owner/qas` |

Owner 详情页复用现有 `/owner/qas/[qaId]` 页面，因此提交后会继续使用 Owner layout 和回答表单。

### 3.2 共享表单设计

`QuestionForm` 增加两个可选路由参数：

- `redirectBasePath`：提交成功后拼接 QA ID 的目标基础路径；
- `newQuestionPath`：提交返回 `401` 时登录页的 `next` 参数。

两个参数默认使用 Family 路由，保持现有调用方和 Family 行为不变。Owner 新增独立页面传入 Owner 路由参数，避免在同一个 Family 页面中通过查询参数混合两种区域语义。

### 3.3 数据与接口影响

本次仅调整 Next.js 前端页面链接和客户端跳转。继续调用原有 QA 创建接口，不改变请求体、响应结构、认证方式、CSRF 处理或后端权限校验；无需 Alembic Migration。

## 4. 实现内容（Implementation）

- 新增 `frontend/src/app/owner/qas/new/page.tsx`，复用 `QuestionForm`。
- 修改 Owner 工作台和 Owner 问答管理页的提问入口为 `/owner/qas/new`。
- 为 `QuestionForm` 增加区域化成功跳转和登录回跳配置。
- 保持 Family 提问页、Family 入口和 Family 提交后的详情路径不变。
- 增加 Owner 页面链接和 Owner 提交跳转的回归测试。

## 5. 验收与测试（Acceptance & Testing）

| 验收类别 | 验证内容 |       结果        |
| --- | --- |:---------------:|
| Owner 入口 | 工作台、Owner 问答管理页的“提出问题”指向 `/owner/qas/new` |      Pass       |
| Owner 提问页 | 返回和取消均指向 `/owner/qas` |      Pass       |
| Owner 提交 | 创建成功后跳转 `/owner/qas/:qaId` 并刷新页面 |  Pass（Vitest）   |
| Family 兼容性 | Family 创建成功后仍跳转 `/family/qas/:qaId` |  Pass（Vitest）   |
| 登录回跳 | `401` 时根据当前区域回到对应提问页 | Pass（类型检查与代码验证） |
| 受影响前端测试 | 3 个测试文件、13 项测试 |      Pass       |
| 前端完整 Vitest | 29 个测试文件、88 项测试 |      Pass       |
| TypeScript 类型检查 | `npm run typecheck` |      Pass       |
| 前端 Lint | `npm run lint` |      Pass       |
| 生产构建 | `npm run build`，包含 `/owner/qas/new` |      Pass       |
| 浏览器端到端 | Owner 提问到回答的完整 Playwright 流程 |      Pass       |

## 6. 遗留风险与后续事项（Risks & Follow-ups）

| 风险 / 遗留事项 | 当前处理 | 后续方向 |
| --- | --- | --- |
| 浏览器端真实工作流尚未验证 | Vitest、类型检查、Lint 和生产构建均已通过 | 启动本地前后端及测试账号后执行 Owner 提问、查看详情和回答的 Playwright 流程 |
| Family 与 Owner 使用不同提问入口 | 通过独立页面和配置化表单明确区分 | 若未来需要跨区域切换，再单独设计统一的区域切换交互 |

