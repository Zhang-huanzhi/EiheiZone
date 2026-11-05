---
id: T001
title: 文档标准化与 v1.4 收口
type: docs
status: Accepted
created: "2026-10-30"
updated: "2026-11-05"
branch: null
---

# T001 文档标准化与 v1.4 收口

> 原分支已合并删除。v1.5 尚未封箱，本任务留在 `docs/tasks/`，封箱时再移入 `docs/versions/`。正文保留 2026-10-30 的原始记录；路径变化以当前规范为准（`iterations/` → `tasks/`，`_附件_` → `assets/`）。

## 1. 背景与目标

`v1.4` 的实现分散在多次提交与历史记录中，根目录 README、现行架构和运维文档仍残留 `v1.1` 的过时描述，同时文档状态与模板字段偏多。本次任务将 `v1.4` 已完成项与延期项分开归档，统一现行文档基线，并把迭代模板简化为「必填 + 按需裁剪」的轻量结构。

## 2. 范围与不做事项

### 本次范围

- 归档 `v1.4` 已完成迭代至 `docs/versions/v1.4/`（008 标记为 `Accepted`），移除 `docs/iterations/v1.4/` 冗余入口；
- 将 `006` 转入 `docs/iterations/backlog/` 并标记 `Deferred`，明确保留未完成边界；
- 简化迭代状态为 `In Progress` / `Accepted` / `Deferred` 三种，更新可裁剪迭代模板与 PR 模板；
- 更新 `AGENTS.md`、`docs/README.md`、`docs/architecture.md`、`docs/operations.md`、`docs/development-process.md` 及三语根目录 README；
- 在 `AGENTS.md` 的计划规则中补充较大技术方案的取舍要求（ADR 机制后来在 T003 中移除）；
- 扩大 `main` push 的部署忽略范围：根目录 README、`AGENTS.md`、PR 模板和 GitHub workflow 不再触发生产部署；
- 补充生产容器架构图与迭代开发流转图（`.puml` 源码及 `.svg` / `.png` 渲染图）。

### 不做事项

- 不继续实施 `006` 的每日备份 cron 或自动告警；
- 不重写 `docs/versions/v1`–`v1.3` 已冻结的历史文档正文；
- 不修改应用代码、API、数据库 Migration、依赖、服务器或外部服务。

## 3. 验收标准

- [x] `docs/versions/v1.4/README.md` 明确列出完成项、`006` 延期项和 `008` `Accepted` 证据；
- [x] 迭代状态收敛为 3 种，模板改为「3 项必填 + 3 项按需」；多种实现方式用短文或简表记下取舍，不要求加权决策矩阵；
- [x] `AGENTS.md`、开发流程文档、迭代规则和 PR 模板使用同一命名与状态约定；
- [x] 架构文档、运维文档和三语根目录 README 与当前模块、Compose 服务、Migration `f1a2b3c4d5e6` 及能力边界一致；
- [x] `006` 标记为 `Deferred`，未被现行入口描述为已持续运行的备份服务；
- [x] 架构图与迭代流转图包含 `.puml` 与可直接渲染的图片（`.svg` / `.png`）；
- [x] Markdown 相对链接与 `git diff --check` 检查通过。

## 4. 方案与技术影响

| 方案 | 取舍结论 |
| --- | --- |
| 只改总索引，不移动 `v1.4` 文件 | **不选**：`iterations/` 与 `versions/` 混放已完成版本，活动目录越来越乱 |
| 重写全部历史版本文档并强制 8 节模板 | **不选**：破坏历史证据，且空表和过多状态增加日常维护负担 |
| 归档 `v1.4`、精简 3 状态与可裁剪模板、只更新现行入口 | **采用**：历史版本保持冻结，日常只维护 4 处现行入口与轻量迭代单 |

- 文档结构：已完成 `v1.4` 迭代移入 `docs/versions/v1.4/`，`006` 移入 `docs/iterations/backlog/`，删除 `docs/iterations/v1.4/` 跳转目录；
- 架构与运维事实：包含 `notification-worker` 和 `media-cleanup-worker`，当前 Migration head 为 `f1a2b3c4d5e6`；COS 备份脚本与隔离恢复演练已完成，但每日 cron 尚未安装；
- 代码与部署：无代码、数据库 Migration 或生产配置变更。

## 5. 实现与测试记录

| 检查 | 结果 | 证据 |
| --- | --- | --- |
| 短期分支检查 | `PASS` | 原分支已合并并删除 |
| 文档与图表更新 | `PASS` | 现行文档、模板、三语 README 与 `docs/_附件_/` 图表已同步 |
| Markdown 相对链接检查 | `PASS` | 仓库内 `docs/`、根目录 README 与 `.github/` 相对路径校验通过 |
| `git diff --check` | `PASS` | 无空白错误或冲突标记 |
| 非运行时路径跳过部署 | `未验证` | `ci.yml` 的 `paths-ignore` 已写入；GitHub 上尚未出现一次被跳过的 `main` push |

## 6. 遗留风险与后续事项

- `006` 后续若启用每日 cron 与备份告警，按 `docs/standards/branching-and-tasks.md` 新建任务和分支，先确认部署脚本修复，再安装定时任务并补齐持续运行验收。
