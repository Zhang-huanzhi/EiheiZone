# 002：Family 成员发布近况与作者展示（Family Post Publishing）

| 项目 | 内容 |
| --- | --- |
| 目标版本 | v1.1.0 |
| 状态 | Accepted |
| 分支 | `feat/post-family-permission` |
| 功能提交 | `93727d7` |
| 完成日期 | 2026-08-09 |
| 数据库迁移 | 无 |

## 1. 需求与范围（Requirements & Scope）

近况原先只能由 Owner 发布，Family 成员无法主动记录家庭动态。本次迭代将发布边界扩展到 Family，同时沿用 001 的图片上传、图片绑定和可见范围能力。为了使家庭成员发布的内容可辨识，所有 Post 读取接口和展示页面都增加发布人昵称。

本次交付包含：

- Family 与 Owner 均可创建文字或图文 Post，每条 Post 最多 9 张图片；
- Family 可选择 `family` 或 `public` 可见范围，默认 `family`；
- Family 近况列表提供发布入口，发布成功回到 `/family/posts`；
- 所有公开、Family 和 Owner 的 Post 展示点显示“发布人：昵称”；
- Owner 保留对所有 Post 的编辑、删除和管理权限，包括 Family 创建的 Post。

本次明确不允许 Family 编辑或删除任何 Post，不增加作者名称快照、审核流程、新 API 路径或数据库字段。用户改名后，历史 Post 会显示新的昵称；这符合当前读取实时用户资料的产品选择。

## 2. 核心决策矩阵（Decision Matrix）

| 编号 | 决策主题 | 优先级 | 确认结果 | 说明 |
| --- | --- | :---: | --- | --- |
| D01 | 发布角色 | P0 | Owner、Family 均可创建 Post 和上传图片 | 路由依赖与服务层均校验角色，避免绕过 HTTP 层调用服务时失去授权保护。 |
| D02 | 管理角色 | P0 | 编辑、删除仍为 Owner-only | Family 只获得创建权，不因 `author_id` 获得本人 Post 的管理权。 |
| D03 | 可见范围 | P0 | Family 可选 `family`、`public`，默认 `family` | 不改变原有公开/家庭读取规则和 Post 数据结构。 |
| D04 | 图片归属 | P0 | 图片只能由上传者本人绑定 | 继续使用 `post_images.owner_id` 限制 pending 图片归属，图片限制沿用 001。 |
| D05 | 作者数据 | P0 | 复用 `posts.author_id -> users.id`，返回昵称 | API 返回稳定的 `author_id` 与 `author_display_name`；UI 只显示昵称，不暴露 `login_name`。 |
| D06 | 查询性能 | P1 | 列表、详情关联预加载作者 | Repository 使用 `joinedload(Post.author)`，避免为每条 Post 额外查询用户。 |

## 3. 详细设计契约（Detailed Design）

### 3.1 权限矩阵

| 操作 | 匿名 | Family | Owner |
| --- | :---: | :---: | :---: |
| 读取公开 Post | 允许 | 允许 | 允许 |
| 读取家庭 Post | 拒绝 | 允许 | 允许 |
| 创建 Post | 拒绝 | 允许 | 允许 |
| 上传并绑定本人 pending 图片 | 拒绝 | 允许 | 允许 |
| 编辑任意 Post | 拒绝 | 拒绝 | 允许 |
| 删除任意 Post | 拒绝 | 拒绝 | 允许 |

写入请求继续要求有效 Cookie 会话和 CSRF Token。Family 尝试调用 `PATCH`、`DELETE /api/v1/posts/{post_id}` 时返回 `403`；匿名写入请求返回 `401`。

### 3.2 数据与接口契约

不新增表或 Migration。Post 已有的 `author_id` 是到 `users.id` 的外键，本次将 `Post.author` 关系用于响应转换；创建时同时写入 `author_id=user.id` 和 `author=user`，确保创建响应可立即取得作者信息。

| 方法与路径 | 授权与请求 | 返回 / 行为 |
| --- | --- | --- |
| `POST /api/v1/posts` | Owner 或 Family；有效 CSRF；标题、正文、`visibility`、可选 `image_ids` | `201`，创建者写入 `author_id`；Family 仅可提交 `family` 或 `public`。 |
| `POST /api/v1/uploads/image` | Owner 或 Family；有效 CSRF；multipart `file` | `201`，生成属于当前用户的 `pending` 图片。 |
| `PATCH /api/v1/posts/{post_id}` | Owner；有效 CSRF | 保持 Owner-only，不因作者身份放宽。 |
| `DELETE /api/v1/posts/{post_id}` | Owner；有效 CSRF | 保持 Owner-only，可删除 Family 创建的 Post。 |
| Post 列表、详情接口 | 按既有可见范围读取 | `PostResponse` 额外返回 `author_id`、`author_display_name`。 |

`author_display_name` 直接读取 `users.display_name`。响应转换集中在 `_to_response()`，作者关系缺失或昵称无效时会拒绝构造不完整的响应；不返回 `login_name`、密码或其他内部用户字段。

### 3.3 前端工作流

Family 从 `/family/posts` 的“发布近况”入口进入 `/family/posts/new`。该页复用 Owner 的 `PostForm`：标题、正文、可见范围、最多 9 张图片的预览、压缩、上传和图片绑定流程一致；区别仅为成功路径与返回路径均为 `/family/posts`。

`PostRecord` 同步接收作者字段。公开列表与详情、Family 列表与详情、家庭首页摘要、Owner 管理列表统一沿用既有时间和可见范围元数据样式展示“发布人：`author_display_name`”。Owner 的编辑和删除入口保持不变。

## 4. 验收与测试（Acceptance & Testing）

| 验收类别 | 验证内容 | 结果 |
| --- | --- | :---: |
| 后端服务与权限 | Family/Owner 创建、Family 禁止编辑删除、Owner 管理 Family Post、图片归属和 CSRF 边界 | Pass |
| API 契约 | `PostResponse` 作者字段；公开与登录接口返回昵称且不泄露 `login_name` | Pass |
| 前端回归 | Family 新建页路径、可见范围和图片字段；各列表/详情/Dashboard/Owner 管理页作者展示 | Pass |
| 自动化检查 | 后端 pytest 232 项、Ruff；前端 Vitest 85 项、类型检查、Lint、生产构建 | Pass |
| 本机 E2E | Family 创建 `family` Post、作者展示、Owner 管理展示和删除、桌面/移动端布局 | Pass（Playwright 2 项，1.6 分钟） |
| VPS 部署验证 | backend、db 健康；frontend、Caddy 运行；健康接口、首页、登录页和公开 Post API 可用 | Pass |
| 人工业务验收 | Family 图文、`public` 可见范围、作者昵称；Owner 编辑 Family Post | Pass |

`frontend/e2e/run-local.ps1` 已修复测试成功后重复 `Pop-Location`、导致临时服务清理无法完成的问题；重跑后脚本能够正常退出并释放 `8100`、`3100` 测试端口。

## 5. 发布记录（Release Record）

2026-08-09 14:37（Asia/Shanghai）将提交 `93727d7` 部署到 VPS。部署使用由该提交生成的 Git 归档，未携带本地 `.env`、未提交文档或构建产物。

部署前已在 VPS 保留排除生产 `.env` 的时间戳源码备份；PostgreSQL、媒体 Docker named volume 和 Caddy 数据均未重置。本次不涉及 Migration。

人工验收已确认 Family 图文 Post、`family`/`public` 可见范围、作者昵称，以及 Owner 编辑 Family Post 均符合预期。本次迭代作为正式功能验收完成。
