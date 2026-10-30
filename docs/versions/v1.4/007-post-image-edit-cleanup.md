# V1.4 / 007：Post 图片编辑与媒体清理自动化

| 目标版本 | `v1.4` |
| --- | --- |
| 状态 | Accepted |
| 日期 | 2026-10-28 |
| 分支 | `feat/v1.4-007-post-image-edit-cleanup` |

## 1. 目标

支持 Owner 编辑已发布 Post 的图片，完成图片新增、删除和九宫格顺序调整；将未关联和删除失败图片的人工清理改为可 dry-run、可统计、可重试的定时任务，并通过微信通知活跃 Owner。

## 2. 本次范围

- `PATCH /api/v1/posts/{post_id}` 支持完整 `image_ids` 列表替换。
- 前端编辑页支持图片添加、删除、上移、下移和拖拽排序。
- 清理脚本支持 `--dry-run`、`--scan-orphans`、`--max-items` 和 JSON 统计。
- 增加媒体清理运行记录、重试字段、孤立文件扫描和独立 `media-cleanup-worker`。
- 清理失败通过现有微信 outbox 通知活跃 Owner；当前项目实际为 `zzk`。

## 3. 不做事项

- 不调整图片裁剪焦点，不改变图片格式和媒体存储方式。
- 不开放 Family 编辑已发布 Post。
- 不增加公开清理 API。

## 4. 技术方案

图片列表以完整数组提交，数组顺序写入现有 `post_images.position`。被移除图片立即尝试删除文件，失败时保留 `cleanup_pending` 并由 worker 重试。清理任务默认以 24 小时宽限期扫描过期 pending 记录和媒体目录孤立文件，统计结果写入 `media_cleanup_runs`。

### 清理配置

| 配置 | 默认值 | 说明 |
| --- | ---: | --- |
| `MEDIA_CLEANUP_WORKER_INTERVAL_SECONDS` | `604800`（7 天） | worker 执行周期；个人项目低频运行，允许孤儿文件暂存 |
| `MEDIA_CLEANUP_ORPHAN_GRACE_HOURS` | `24` 小时 | 文件超过该宽限期后才会进入清理候选 |
| `MEDIA_CLEANUP_MAX_ITEMS` | `1000` | 单次最多处理的数据库记录和孤立文件 |
| `--dry-run` | 关闭 | 只扫描和输出统计，不删除文件或数据库记录 |
| `--scan-orphans` | 手工脚本显式开启；worker 默认开启 | 扫描媒体目录中没有数据库记录的文件 |
| 失败告警 | 活跃 Owner | 通过现有微信 outbox 发送；当前项目接收者为 `zzk` |

新增 Migration：`f1a2b3c4d5e6`。

## 5. 验收标准

- Owner 可以新增、删除、重排已发布 Post 图片，纯排序变更也可保存。
- 重复、越权、超过 9 张和超过总大小的图片列表被拒绝。
- dry-run 不修改数据库或文件；正式任务删除过期记录、扫描并删除孤立文件，失败项可重试。
- 清理失败运行记录可查询，且微信通知只发送给活跃 Owner。
- 后端 Ruff、前端 ESLint/TypeScript 通过；相关测试在专用测试库 Migration 完成后通过。

## 6. 实现与测试记录

| 检查 | 结果 | 说明 |
| --- | --- | --- |
| Backend Ruff | Pass | `ruff check backend/app backend/scripts` |
| Frontend ESLint | Pass | `npm run lint`（现有测试文件有 1 条未使用参数 warning） |
| Frontend TypeScript | Pass | `npx tsc --noEmit --incremental false` |
| Migration | Pass | 专用 `eiheizone_test` 已升级到 `f1a2b3c4d5e6` |
| Backend tests | Pass | 专用 `eiheizone_test`：完整套件 267 passed；首次运行前已升级新 Migration |
| Frontend tests | Pass | Vitest：114 passed |
| Lifecycle diagram | Pass | 按 `notes/文档规范/图 风格&主题/确定.md` 重新导出 PlantUML PNG |

## 7. 遗留风险

- 清理通知依赖现有微信配置和 Owner 绑定状态；通知关闭时仍保留运行记录和日志。
- 微信告警的实际发送仍需要部署环境开启微信通知并完成 Owner 绑定；这属于部署前置条件，不影响清理记录和失败重试。
