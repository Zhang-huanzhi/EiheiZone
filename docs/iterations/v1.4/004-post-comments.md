# V1.4 / 004 Post 评论

| 项目 | 内容 |
| --- | --- |
| 目标版本 | `v1.4` |
| 状态 | Accepted |
| 日期 | 2026-10-16 |
| 分支 | `feat/v1.4-004-post-comments` |

## 前言

Sister 需要在家庭近况下补充简单讨论能力。本迭代为 Post 增加登录用户可用的扁平文本评论，不扩展为通用社交互动系统。

## 1. 目标

- Family 和 Owner 可以查看有权限 Post 的评论并发表评论；
- 评论作者和 Owner 可以删除评论；
- 评论按独立资源分页，Post 删除时级联删除评论。

## 2. 本次范围

- 新增 `post_comments` 表、约束、外键和分页索引；
- 新增 `GET/POST /api/v1/posts/{post_id}/comments` 与 `DELETE /api/v1/posts/{post_id}/comments/{comment_id}`；
- 评论正文限制为 1–2000 个字符，拒绝纯空白文本；
- Family Post 详情页与 Owner Post 编辑页展示评论、发布表单和删除操作；
- 公共 Post 页面不读取、不显示评论。

## 3. 不做事项

- 不支持嵌套回复、编辑、点赞、提及、Markdown/HTML、附件或匿名评论；
- 不发送评论通知，不把评论列表或评论数嵌入 Post 和 Dashboard 响应；
- 不开放独立评论管理页面。

## 4. 技术方案与接口

- 评论归属于现有 `posts` 模块，沿用 `router -> service -> repository` 分层；
- 读取和写入要求 Family/Owner 会话，并先验证 Post 可见性；不存在或不可见的 Post 返回 `POST_NOT_FOUND`；
- 写入和删除要求绑定当前会话的 CSRF Token；删除权限由 Service 强制校验作者本人或 Owner；
- 评论列表使用统一 `Page` 结构，默认 `limit=20`，最大 `100`，按 `created_at DESC, id DESC` 排序；
- 响应只返回作者昵称、正文和时间等客户端所需字段，不返回登录名。

## 5. 影响范围

- 后端 Post 模型、Schema、Repository、Service、Router 与 Alembic Migration；
- 后端 Post 评论权限、Schema、Migration 和级联删除测试；
- 前端评论类型、API、Server loader、评论组件、Family 详情页和 Owner 编辑页；
- README 能力说明和本迭代文档。

## 6. 验收标准

1. 匿名用户不能读取或发布评论；Family/Owner 只能访问自己有权限的 Post 评论。
2. Family/Owner 可以发布合法文本评论；空白和超过 2000 字符的正文被拒绝。
3. 评论作者可以删除自己的评论，Owner 可以删除任意评论，其他 Family 用户返回 `403`。
4. 公共 Post 页面不显示评论；Family 详情页和 Owner 编辑页显示分页评论与操作表单。
5. 删除 Post 后评论记录级联删除，Migration 可从当前 head 升级和降级。

## 7. 实现与测试记录

| 检查 | 结果 | 证据 |
| --- | --- | --- |
| 后端 Ruff | PASS | `ruff check app tests/posts tests/integration` 通过 |
| 后端 Pytest | PASS | 管理员 PowerShell 下完整回归 `265 passed in 23.42s`；评论、权限、图片和 Migration 测试全部通过 |
| 前端 Vitest | PASS | 35 test files / 109 tests passed |
| 前端 TypeScript/Lint/Build | PASS（Lint 有既有 warning） | TypeScript 与 Next.js build 通过；Lint 仅报告 `post-images.test.tsx` 的既有未使用参数 warning |
| Playwright | PASS | 手动验证 Family 发布/删除、Owner 删除任意评论、公共页面不可见评论 |

## 8. 遗留风险

- 当前测试和 Migration 验证依赖专用 PostgreSQL 测试数据库；
- Windows/Codex 受限终端可能无法访问 pytest 临时目录；使用普通或管理员 PowerShell 运行测试即可，已完成本次完整回归。
