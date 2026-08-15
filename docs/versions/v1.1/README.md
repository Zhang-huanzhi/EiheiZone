# EiheiZone v1.1.0 历史交付

| 产品版本 | `v1.1.0` |
| --- | --- |
| 计划发布日期 | 2026-08-15，以实际 tag 创建记录为准 |
| 状态 | Release Candidate / Accepted |
| 对应 GitHub 交付 | 合并并完成生产验证后创建 `v1.1.0` tag 和 GitHub Release |

本目录归档 V1 之后的五次增量迭代。它们共同构成 `v1.1.0`：增加 Post 图片和 Family 发布能力，完善 QA 展示与 Owner 路由上下文，并建立 GitHub Actions、SSH、Docker Compose 自动发布和可回滚链路。

## 版本内容

| 顺序 | 迭代 | 主要结果 |
| --- | --- | --- |
| 001 | [`001_post_image.md`](001_post_image.md) | 每条 Post 最多 9 张图片，后端重编码、鉴权读取并保存到 `media_data`。 |
| 002 | [`002_post_family_permission.md`](002_post_family_permission.md) | Family 可发布图文 Post，全部展示点返回并显示作者昵称，Owner 保留管理权。 |
| 003 | [`003_github_ssh_cicd.md`](003_github_ssh_cicd.md) | PR 质量门禁、`main` 自动部署、稳定 commit 记录和人工回滚。 |
| 004 | [`004_qa_showUpdate.md`](004_qa_showUpdate.md) | QA 列表与 Family 首页显示回答时间。 |
| 005 | [`005_qa_owner_context_fix.md`](005_qa_owner_context_fix.md) | Owner 提问、详情和回答保持在 `/owner/qas/*` 区域。 |

## 对外契约与兼容性

- Family 与 Owner 均可创建文字或图文 Post；只有 Owner 可以编辑或删除任意 Post；
- 图片上传使用 `POST /api/v1/uploads/image`，Post 创建请求可带 `image_ids`；
- 图片读取使用 `GET /api/v1/media/images/{image_id}`，权限跟随关联 Post；
- Post 响应增加作者与图片信息；QA 继续使用既有 `answered_at` 字段，不增加 QA API；
- Owner 与 Family 使用独立的 QA 页面路由，但复用同一后端接口和表单能力；
- 除新增 PostImage 数据结构外，V1 API、角色和既有纯文字 Post 保持兼容。

## Migration 与配置影响

| 项目 | v1.1.0 影响 |
| --- | --- |
| 数据库 | 新增 `c18f6a72d901_create_post_images.py`，建立 `post_images` 表。 |
| 持久化 | Compose 新增 `media_data:/app/media`，必须与 PostgreSQL 一起备份。 |
| 应用配置 | `MEDIA_ROOT` 可覆盖默认媒体目录；生产 Compose 使用 `/app/media`。 |
| GitHub | 需要 `production` Environment、五项 SSH Secrets 和 `main` 分支保护。 |
| 生产服务器 | 需要 `/opt/eiheizone`、生产 `.env`、`.deploy/` 状态和部署 SSH 公钥。 |

## 发布验证

五份迭代记录保存各自完成时的自动化测试、部署和人工验收证据。2026-08-15 在归档分支执行了统一回归：

| 检查 | 实际结果 |
| --- | --- |
| 后端 | Ruff 通过；pytest 232/232 通过。 |
| 前端 | Vitest 29 个文件、88/88 项通过；ESLint、TypeScript 类型检查、Next.js production build 通过。 |
| 浏览器 | Playwright 2/2 通过；覆盖 Owner 提问与回答的 `/owner/qas/*` 闭环、Family 兼容路径和桌面/移动端溢出检查。 |
| 文档 | `docs/` 本地 Markdown 链接全部可解析；两张 PlantUML 导出图已视觉检查，无乱码、裁切或重叠。 |
| 测试环境清理 | Playwright 正常退出，临时端口 `3100`、`8100` 已释放。 |

Pull Request required checks、合并后的 Production Deploy workflow、线上冒烟验证和 `v1.1.0` tag 尚未执行，必须由仓库维护者按发布顺序完成；任一步失败都阻止 tag。

## 已知限制

- 已发布 Post 暂不支持增删或重排图片；
- 超过 24 小时未绑定的图片依赖维护脚本按需清理，尚未配置定时任务；
- 健康检查失败路径没有在唯一生产环境主动注入，待 staging 环境补测；
- PostgreSQL 和 `media_data` 尚无异机加密备份与定期恢复演练，VPS 整机损坏仍可能造成永久数据丢失；
- 自动回滚不会逆向执行数据库 Migration，破坏性数据变更必须单独设计发布与恢复方案。

当前开发、架构和运维规则以 [`../../development-process.md`](../../development-process.md)、[`../../architecture.md`](../../architecture.md) 和 [`../../operations.md`](../../operations.md) 为准。
