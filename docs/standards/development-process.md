# 当前开发流程

> 当前基线：T003 重构后（2026-11-05）；产品基线 `v1.5`。

本文档说明日常任务、检查、发布和文档同步方式。分支命名、任务编号与发版封箱规则见 `docs/standards/branching-and-tasks.md`，此处不重复定义。V1 初期的六阶段流程归档在 `docs/versions/v1/00b_v1_development_process.md`，不再作为日常模板。

## 1. 日常闭环

1. 在 `docs/tasks/` 用 `docs/tasks/_template.md` 新建 `NNN-kebab-topic.md`，填写 frontmatter 以及「背景与目标」「范围与不做事项」「验收标准」。
2. 从最新 `main` 切出 `<type>/<NNN>-<kebab-topic>` 分支；同一任务的后续修改留在该分支。
3. 实现代码、测试、Migration 和受影响的现行文档；任务文档只记录真实检查结果。
4. 用 `<type>(<scope>): <summary> [TNNN]` 建 PR，链接任务文档，说明范围、数据/部署影响、验证结果与遗留风险。
5. `Backend`、`Frontend`、`Deployment artifacts` 三项 required checks 通过后合并到 `main`；合并后立即删除分支。
6. 任务状态改为 `Accepted`，留在 `docs/tasks/`；状态为 `Deferred` 的任务同样留在 `docs/tasks/`，写明已验证到哪一步、哪些能力尚未生效。

不改变外部行为的小错字或局部维护，可直接写在提交与 PR 中，不必新建任务文档。

做计划时，如果方案会影响多个模块、部署、安全或数据边界，或者以后的任务还得重做这个决定，就把取舍和影响范围写进任务文档。

## 2. Pull Request 与部署

- PR 标题使用 `<type>(<scope>): <summary> [TNNN]`。
- `Backend`、`Frontend`、`Deployment artifacts` 三项 required checks 全部通过后才可合并。
- 合并到 `main` 后，运行时代码、部署脚本和会进入站点的静态资源才会再次触发 `main` CI 与生产自动部署。只包含 `docs/**`、根目录三份 README、`AGENTS.md`、`.github/pull_request_template.md` 或 `.github/workflows/**` 的 push 在 PR 阶段完成检查，合并后不触发生产部署。

## 3. 发版封箱

当需要发布新版本、且已积累若干 `Accepted` 任务时，按 `docs/standards/branching-and-tasks.md` 第 6 节执行：

1. 新建 `docs/versions/<版本号>/`，只移动 `Accepted` 任务文档；`In Progress`、`Deferred` 留在 `docs/tasks/`。
2. 写 `docs/versions/<版本号>/README.md`，汇总完成项、Migration、验证证据和未包含能力。
3. 更新 `docs/README.md` 与 `docs/versions/README.md` 入口，不保留空壳旧版本目录。
4. 归档 PR 合并、生产部署（如涉及代码）和健康检查通过后，在对应 `main` 提交上创建 annotated tag（如 `v1.5`）和 GitHub Release。

## 4. 变更同步清单

| 变更内容 | 同步更新位置 |
| --- | --- |
| 新功能或缺陷修复 | 代码、回归测试、当次任务文档或 PR 验证记录 |
| 数据库结构变化 | Alembic Migration、专用测试库升级验证记录 |
| 系统组件或数据契约变化 | `docs/architecture.md` |
| 部署、回滚、备份或清理方式变化 | `docs/operations.md` |
| 影响多个模块、部署、安全或数据边界，或以后还会重做的技术选择 | 写入当次任务文档的「方案与技术影响」 |
