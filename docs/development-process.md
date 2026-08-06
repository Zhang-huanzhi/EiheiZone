# 当前开发流程

| 适用产品版本 | Current / v1.x |
| --- | --- |
| 文档状态 | Active |
| 最后更新 | 2026-08-06 |

本文档描述 V1 之后的轻量开发流程。V1 当时采用的六阶段流程仍保存在 [`versions/v1/00b_v1_development_process.md`](versions/v1/00b_v1_development_process.md)，不作为后续迭代的强制模板。

## 1. 一次迭代

一次功能或一组相关变更使用一份 `iterations/` 文档，记录目标、范围、不做事项、技术选择、影响、验收、测试和发布结果。小修正可以直接记录在提交说明中，不需要新建完整文档。

## 2. Git 工作流

1. 从最新 `main` 创建短期分支，例如 `feat/post-image`、`fix/session-expiry` 或 `docs/update-process`。
2. 在分支中完成代码、测试、Migration 和必要的文档更新。
3. 运行受影响的后端、前端和浏览器检查。
4. 推送分支并通过 Pull Request 合并回 `main`。单人项目也保留 Pull Request，作为变更说明和自检记录。
5. 迭代完成但尚未发布时，不创建产品 tag。
6. 准备正式交付时，在合并后的提交上创建 `v1.1.0` 等 tag，并建立对应的 GitHub Release。

`main` 应保持可运行和可发布。V1 文档不回填 V1.1 内容；V1.1 的新需求和实现记录写入新的迭代文档。

## 3. 变更规则

| 变化 | 必须留下的记录 |
| --- | --- |
| 新功能或缺陷修复 | 代码、测试和迭代文档中的结果 |
| 数据库结构变化 | 新的 Alembic Migration 和 Migration 测试 |
| 当前架构摘要变化 | 更新 `architecture.md` |
| 部署、备份或恢复方式变化 | 更新 `operations.md` |
| 跨模块或长期架构取舍 | 新增 `adr/` 文档，并从迭代文档链接 |

## 4. 提交和发布

提交信息使用简短的 Conventional Commits，例如：

```text
feat(posts): add post image reference
test(posts): cover image visibility
docs(iteration): record post image workflow
```

产品版本遵循以下约定：

```text
v1.0.0  V1 正式交付
v1.1.0  向后兼容的新功能
v1.1.1  缺陷、安全或依赖修复
v2.0.0  不兼容的权限、API 或架构变化
```

正式部署记录 tag、Git commit、Migration、测试结果、部署时间和遗留风险。生产环境不使用未标记的临时提交作为长期部署依据。
