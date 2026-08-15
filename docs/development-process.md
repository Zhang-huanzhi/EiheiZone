# 当前开发流程

| 适用产品版本 | Current / v1.1.x |
| --- | --- |
| 文档状态 | Active |
| 最后更新 | 2026-08-15 |

本文档描述 V1 之后的轻量迭代与发布流程。V1 当时采用的六阶段流程保存在 [`versions/v1/00b_v1_development_process.md`](versions/v1/00b_v1_development_process.md)，不作为后续迭代的强制模板。

## 1. 迭代生命周期

| 阶段 | 文档状态 | 退出条件 |
| --- | --- | --- |
| 提议 | Proposed | 目标、范围、不做事项和验收标准明确。 |
| 实施 | In Progress | 代码、Migration、测试和必要文档在短期分支中同步更新。 |
| 验收 | Accepted | 受影响检查与业务验收完成，实际结果和遗留风险已记录。 |
| 归档 | Released / Frozen | 同一产品版本的迭代已汇总到 `versions/v1.x/`，合并、部署和 tag 可追踪。 |

一次功能或一组相关变更使用一份 `iterations/v1.x/` 文档，记录目标、范围、技术选择、影响、验收、测试和发布事实。小错字或不改变外部行为的局部维护可以只记录在提交与 PR 中。

## 2. 分支与 Pull Request

1. 从最新 `main` 创建短期 `feat/`、`fix/` 或 `docs/` 分支。
2. 在同一分支完成代码、测试、Migration 和受影响文档，禁止回填已经冻结的旧版本范围。
3. 本地运行受影响检查；涉及共同契约或正式发布时执行完整检查。
4. 推送分支并创建 Pull Request，说明行为变化、Migration/配置影响、测试结果和遗留风险。
5. `Backend`、`Frontend`、`Deployment artifacts` required checks 全部成功且分支与 `main` 同步后才可合并。

GitHub Actions 对 Pull Request 和 `main` push 运行 CI。`main` 应始终保持可运行、可迁移和可发布；测试失败、文档证据矛盾或尚未验证的发布条件不得写成 Pass。

## 3. 版本归档

当同一目标版本的迭代全部 Accepted 后：

1. 创建 `versions/v1.x/README.md`，汇总版本能力、阅读顺序、Migration、配置影响、验证证据和遗留风险；
2. 将整个 `iterations/v1.x/`（包括 `_附件_/`）移动到 `versions/v1.x/`，保持迭代文件名和相对链接稳定；
3. 修正当前文档、仓库 README 和其他入口链接，`iterations/README.md` 继续服务后续活动版本；
4. 统一版本号、状态和互相矛盾的历史记录，只依据实际代码与已执行验证修正事实；
5. 通过 PR 合并归档提交，不在活动分支或未通过 CI 的提交上创建产品 tag。

## 4. 发布与 tag

1. 归档 PR 合并到 `main` 后，等待该提交的 CI 与 Production Deploy workflow 成功。
2. 验证健康接口、HTTPS、登录及本版本受影响的核心流程。
3. 在已部署且验证通过的 `main` 提交上创建 annotated tag，例如 `v1.1.0`。
4. 推送 tag，并使用版本 README 创建对应 GitHub Release。
5. 发布记录必须能追踪 tag、完整 commit、Migration、自动化检查、部署时间和仍接受的风险。

版本号遵循语义化约定：

```text
v1.0.0  首个正式交付
v1.1.0  向后兼容的新功能
v1.1.1  缺陷、安全或依赖修复
v2.0.0  不兼容的权限、API 或架构变化
```

## 5. 变更记录要求

| 变化 | 必须留下的记录 |
| --- | --- |
| 新功能或缺陷修复 | 代码、回归测试、迭代文档或 PR 中的实际结果 |
| 数据库结构变化 | 新 Alembic Migration、Migration 测试和升级影响 |
| 当前架构摘要变化 | 更新 `architecture.md` |
| 部署、备份或恢复方式变化 | 更新 `operations.md` |
| 跨模块或长期架构取舍 | 新增 `adr/`，并从迭代或版本文档链接 |

提交信息使用简短的 Conventional Commits，例如：

```text
feat(posts): add image support
fix(qas): preserve owner route context
test(e2e): cover owner question workflow
docs: archive v1.1 release
```
