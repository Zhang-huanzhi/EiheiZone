---
id: T003
title: 文档体系与分支规范重构
type: refactor
status: Accepted
created: "2026-11-05"
updated: "2026-11-05"
branch: refactor/003-doc-governance
---

# T003 文档体系与分支规范重构

## 1. 背景与目标

`docs/` 同时存在 `iterations/` 与 `versions/` 两套入口，旧的版本内编号（如 001、006）和分支名里的版本号增加了日常查找成本；完成项、延期项和现行规则分散在多个 README 与模板中。

本次重构建立「`tasks/` 流水暂存 + `versions/` 发版封箱」的单一体系：平时在 `docs/tasks/` 轻量开工，积累到一定程度再按版本归档；编号全局单调递增，分支名不再携带版本号。

## 2. 范围与不做事项

### 本次范围

- 删除 `docs/iterations/`：已完成记录留在 `docs/tasks/`（v1.5 尚未封箱），延期草稿也转入 `docs/tasks/`。
- 将 `docs/_附件_/` 重命名为 `docs/assets/`，保留 `versions/**` 内冻结的版本局部 `_附件_/`。
- 将唯一一份现行 `development-process.md` 移入 `docs/standards/`，根目录不再保留副本。
- 新增 `docs/standards/branching-and-tasks.md`（分支、编号、任务与封箱规则的唯一来源）和 `docs/schemas/task-frontmatter.schema.json`（任务 frontmatter 契约）。
- 新增 `docs/tasks/_template.md`、`docs/tasks/003-doc-governance.md`，并把原 `006` 重编为 `docs/tasks/002-basic-disaster-recovery.md`。
- 本次任务编号为 `T003`；`T001` 保留在 `docs/tasks/`（Accepted），现行文档中的三段版本号统一为 `v1.5`。
- 新增 `docs/versions/README.md`，标注 v1.0–v1.4 为物理冻结的早期资产；v1.5 未封箱，不建版本目录。
- 删除 `docs/adr/`（两个 ADR 与索引）；`docs/` 下现行文档不再引用 ADR，也不使用 Markdown 文档互跳。
- 同步更新 `docs/README.md`、架构/运维文档、三语根目录 README、PR 模板和 `AGENTS.md` 中的路径与规则。
- 冻结版本只做必要的路径、版本号和归档入口编号修正，不改写正文结论。

### 不做事项

- 不创建 `registry.yaml`、任务清单或任何与目录内容重复的索引文件。
- 不重写冻结版本正文结论；历史编号不逐条重编，仅把原 001 记为 `T001`。
- 不修改应用代码、API、数据库 Migration、依赖或 CI 配置。
- 不删除或改名仓库中已存在的其他分支（`docs/002-doc-governance`、示例分支等）。

## 3. 验收标准

- [x] `docs/` 只保留 `README.md`、`architecture.md`、`operations.md`、`assets/`、`standards/`、`schemas/`、`tasks/`、`versions/` 这些现行入口；`docs/iterations/` 和 `docs/adr/` 不存在。
- [x] `docs/` 根目录不再有 `development-process.md`，现行规范只有 `standards/development-process.md` 一份；冻结历史中的 `00b_v1_development_process.md` 保持原样。
- [x] 现行文档与三语 README 中的图片、任务、归档和规范路径一致。
- [x] `docs/` 下的现行文档不使用 Markdown 文档互跳；根目录三语 README 只保留语言切换链接。
- [x] 分支命名、全局编号、任务状态与发版封箱规则只有一个来源，`AGENTS.md`、PR 模板和 `docs/README.md` 与其一致。
- [x] `docs/tasks/` 中任务 frontmatter 符合 `task-frontmatter.schema.json`；`T002` 保留原延期事实并注明重编号。
- [x] 任务编号为 `T003`，`T001` 保留在 `tasks/`（Accepted），等待 v1.5 封箱；现行文档统一使用 `v1.5`。
- [x] `versions/README.md` 明确 v1.0–v1.4 冻结；v1.5 尚未封箱。
- [x] `git diff --check` 通过。

## 4. 方案与技术影响

| 方案 | 取舍结论 |
| --- | --- |
| 保留 `iterations/` 只改索引 | **不选**：两套入口并存，版本内编号继续混淆 |
| 按新版结构整理，任务与版本分层 | **采用**：既有历史可追溯，日常只维护 `tasks/` 与版本封箱 |
| 把现行架构、运维文档也移出 `docs/` 根目录 | **不选**：改动面大，且它们是当前入口而非任务或规范 |
| 重写冻结版本正文以统一命名 | **不选**：破坏历史证据，只修正必要路径、版本号和归档入口编号 |
| 新建 `registry.yaml` 统一索引 | **不选**：与目录内容重复，且需要额外维护 |

- 文档结构：`tasks/` 保存活跃与延期任务，`versions/` 保存封箱版本，`standards/` 保存长期规范，`schemas/` 保存机器契约。
- 编号：`T001` 为 v1.5 文档标准化（Accepted，留在 `tasks/` 等待封箱），`T002` 为原 `006` 延期项，本次为 `T003`；下一条新任务从 `T004` 继续，冻结版本中的旧编号不占用新序列。
- 流程图：旧 `iteration-workflow` 图描述的是已废弃流程，现行流程改用 `branching-and-tasks.md` 中的 Mermaid；旧图文件保留在 `docs/assets/` 作为历史资产，不再被引用。
- 接口、数据结构与 Migration：无。
- 配置、权限或部署影响：无运行时代码变化；纯文档变更合入后不触发生产部署。

## 5. 实施与检查记录

| 检查 | 结果 | 证据 |
| --- | --- | --- |
| 分支创建 | `PASS` | 从 `main`（`1db5b7e`）切出；最终分支为 `refactor/003-doc-governance` |
| 目录迁移与清理 | `PASS` | `docs/iterations/` 已删除；`assets/`、`standards/development-process.md`、`tasks/001-documentation-standardization.md`、`tasks/002-basic-disaster-recovery.md` 就位 |
| 现行文档图片与资源路径检查 | `PASS` | 现行/变更 Markdown 文件的图片、PlantUML/SVG/PNG 路径可解析；现行文档不使用 Markdown 文档互跳 |
| ADR 与互跳清理 | `PASS` | `docs/adr/` 已删除；`docs/` 下现行文档和 `AGENTS.md` 不再引用 ADR，也不串联其他 Markdown |
| `git diff --check` | `PASS` | 无空白错误 |
| schema JSON 语法 | `PASS` | `json.load` 解析成功 |
| 任务 frontmatter 校验 | `PASS` | `T001`/`T002`/`T003` 必填字段、枚举、ID、分支与日期格式通过；`T001`/`T002` 使用 `branch: null` |
| 编号与版本号统一 | `PASS` | `T001` 待封箱、`T002` 延期、`T003` 本次；现行文档使用 `v1.5`，不再使用三段版本号 |
| 残留入口检查 | `PASS` | `iterations`、`adr`、`_附件_` 只出现在冻结归档和规则说明文字中；无 `registry.yaml` |

## 6. 遗留风险与后续事项

- 冻结归档中存在既有断链（如 `versions/v1.2/002-performance-diagnosis` 指向旧 Obsidian 路径），本次只报告、不修改。
- 冻结归档内部仍保留历史文档互链和 ADR 文本，本次未逐条改写；只清理了指向已删除 ADR 的链接和跨到现行文档的入口。
- `docs/assets/architecture-v1.5.png` 仍是旧版本渲染，图内标题未更新；`.puml` / `.svg` 已改为 `v1.5`，需要重新导出 PNG。
- `jsonschema` 未安装，frontmatter 契约暂用内联等价检查；后续若允许增加依赖，可在 PR 检查中加入自动校验。
- 旧 `iteration-workflow` 的 PNG/SVG/PUML 仍保留在 `docs/assets/`，不再被现行文档引用；如需删除应单独确认。
- 仓库中的 `docs/002-doc-governance` 与示例分支未处理，后续按新规则在合并后清理。
- 原 `006` 文档称 `--no-recreate` 与 `cmp` 校验尚未进入 `main`；核对发现两项均已随 #27 进入 `main`，已在 `T002` 增加现状说明，剩余未完成项为每日 cron、自动告警和持续运行验收。
