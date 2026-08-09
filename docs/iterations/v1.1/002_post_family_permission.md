# 002：Family 成员发布 Post

| 项目 | 内容 |
| --- | --- |
| 目标版本 | v1.1.0 |
| 状态 | In Progress |
| 分支 | `feat/post-family-permission` |

## 1. 目标

允许 Family 成员发布近况 Post，并复用现有图片上传和展示能力；所有近况页面同时显示发布人昵称。Family 只拥有创建权限，Post 的编辑和删除继续由 Owner 统一管理。

## 2. 本次范围

- `POST /api/v1/posts` 允许 Family 和 Owner，保留标题、正文、可见范围和图片字段。
- `POST /api/v1/uploads/image` 允许 Family 和 Owner；图片仍只能由上传者绑定。
- Family 可在 `/family/posts/new` 发布文字或图文近况，并选择“仅家人”或“公开”，默认“仅家人”。
- Family 近况列表增加发布入口；Owner 管理页和更新/删除权限保持不变。
- Post API 返回 `author_id` 和 `author_display_name`；公开和登录后的 Post 页面都只显示昵称，不返回 `login_name`。

## 3. 不做事项

- 不允许 Family 编辑或删除 Post。
- 不新增数据库作者字段、作者名称快照、审核流程或新的 API 路径。
- 不修改数据库结构，因此没有 Alembic Migration。

## 4. 技术方案与候选选择

沿用现有 Family/Owner 读取依赖和 CSRF 校验，仅将创建 Post、上传图片的写入边界扩展为 Family/Owner。服务层继续校验角色，避免绕过 HTTP 依赖直接调用时失去权限保护；`post_images.owner_id` 继续限制图片只能由上传用户绑定。Post 作者通过已有 `author_id -> users.id` 关系读取 `display_name`，查询使用关联预加载避免 N+1。

## 5. 影响范围

涉及后端 Posts 响应 Schema、服务、Repository 和模型说明；前端 Post 类型、列表/详情、Dashboard、Owner 管理列表；对应单元、API、权限和 E2E 测试。

## 6. 验收标准

- Family 携带有效 CSRF 可以创建文字 Post 和带图片 Post。
- Family 创建的 Post 按 `family`/`public` 可见范围读取。
- Family 对任意 Post 的 PATCH/DELETE 仍返回 403；Owner 可继续编辑和删除。
- Family 页面有发布入口，创建成功回到 `/family/posts`；Owner 页面行为不回归。
- 公开页、Family 页、Dashboard 和 Owner 管理页均显示正确的发布人昵称，且不显示 `login_name`。

## 7. 实现与测试记录

- 后端 `pytest`：232 项通过；Ruff：通过。
- 前端 Vitest：84 项通过；TypeScript：通过；ESLint：0 errors（保留 2 个既有 coverage warning）；生产构建：通过。
- E2E：尝试执行但被已有 Next.js 开发服务器占用 `.next` 锁阻塞，未完成流程验证；需停止已有开发服务器后重新执行 `frontend/e2e/run-local.ps1`。
- 作者展示：后端作者字段、公开/登录 API 昵称和前端各展示点已补充回归断言。

## 8. 发布记录

暂无。

## 9. 遗留风险

两阶段图片上传在用户取消发布时仍可能留下 pending 图片，沿用 `cleanup_post_images.py` 的既有清理机制。
