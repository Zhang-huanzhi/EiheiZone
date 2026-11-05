# EiheiZone 文档

本目录保存 EiheiZone 的正式工程文档。根目录下的现行文档随系统变化直接更新；`tasks/` 保存活跃任务，`versions/` 保存已封箱并冻结的历史版本；源代码、Migration 和自动化测试以仓库实现为准。

> 当前文档体系基线：T003（2026-11-05）；产品基线 `v1.5`。

## 1. 现行文档

日常开发、运维与架构查阅只看这四处（路径相对 `docs/`）：

| 文档 | 说明 |
| --- | --- |
| `architecture.md` | 当前系统上下文、生产容器架构、模块职责与数据安全边界 |
| `operations.md` | CI/CD、自动部署、回滚、媒体清理与 COS 备份恢复手册 |
| `standards/branching-and-tasks.md` | 分支命名、全局编号、任务生命周期与发版封箱 |
| `standards/development-process.md` | 日常闭环、PR 检查、发布与变更同步 |

## 2. 任务工作区

日常任务在 `tasks/` 一题一档；`In Progress`、`Accepted`（待封箱）和 `Deferred` 任务都留在这里，封箱时再归档：

- 任务模板：`tasks/_template.md`
- frontmatter 契约：`schemas/task-frontmatter.schema.json`
- `T001` 文档标准化与 v1.4 收口（`Accepted`，等待 v1.5 封箱）：`tasks/001-documentation-standardization.md`
- `T002` COS 基础数据防灾（`Deferred`，原 V1.4 / 006）：`tasks/002-basic-disaster-recovery.md`
- `T003` 文档体系与分支规范重构（`Accepted`）：`tasks/003-doc-governance.md`

任务状态只有 `In Progress`、`Accepted`、`Deferred`；完整规则见 `standards/branching-and-tasks.md`。

## 3. 版本归档

`versions/` 只保存已封箱版本，归档后物理冻结。`v1.0`–`v1.4` 是历史归档；`v1.5` 尚未封箱，已完成任务仍留在 `tasks/`。

| 版本 | 归档入口 |
| --- | --- |
| `v1.4` | `versions/v1.4/README.md` |
| `v1.3` | `versions/v1.3/README.md` |
| `v1.2` | `versions/v1.2/README.md` |
| `v1.1` | `versions/v1.1/README.md` |
| `v1.0` | `versions/v1/README.md` |

`v1.5` 封箱时，再把 `tasks/` 中已 `Accepted` 的任务移入 `versions/v1.5/`。

## 4. 图片资源

文档图片与图表源文件集中在 `assets/`；根目录 README 的工作台截图也引用此处。已废弃流程的旧图仅作历史保留，不作为现行流程依据。

## 公开边界

文档不得加入真实 `.env`、数据库备份、家庭数据、SSH 私钥、`signing.keystore`、`signing-key-info.txt`、完整 Android 签名 ZIP 或任何密码。APK/AAB 如需分发，应通过独立受控渠道提供，不与公开源代码和文档混放。
