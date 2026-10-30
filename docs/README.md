# EiheiZone 文档

本目录保存 EiheiZone 的正式工程文档。根目录下的现行文档随系统变化直接更新；`versions/` 保存已验收版本的冻结记录，不随后续功能回填；源代码、Migration 和自动化测试以仓库实现为准。

> 当前文档基线：`v1.5.1`（最后更新：2026-10-30）

## 1. 现行文档

日常开发、运维与架构查阅只看这四处：

| 文档 | 说明 |
| --- | --- |
| [`architecture.md`](architecture.md) | 当前系统上下文、生产容器架构、模块职责与数据安全边界 |
| [`operations.md`](operations.md) | CI/CD、自动部署、回滚、媒体清理与 COS 备份恢复手册 |
| [`development-process.md`](development-process.md) | 分支、迭代生命周期、PR 检查、版本归档与发版流程 |
| [`adr/README.md`](adr/README.md) | 跨模块或长期复用的架构决策记录（ADR） |

## 2. 活动迭代与延期项

新功能或缺陷修复在 `iterations/v1.x/` 中一题一档，版本收口时归档至 `versions/v1.x/`：

- [当前活动版本：`iterations/v1.5/`](iterations/v1.5/README.md)
- [延期工作池：`iterations/backlog/`](iterations/backlog/006-basic-disaster-recovery.md)（保留已验证证据，不计入已交付能力）
- [迭代编写规则](iterations/README.md) 与 [可裁剪模板](iterations/_template.md)

## 3. 历史版本归档

| 版本 | 归档入口 | 核心交付 |
| --- | --- | --- |
| `v1.4` | [`versions/v1.4/README.md`](versions/v1.4/README.md) | 微信测试号通知、Post 扁平评论、已发布 Post 图片编辑与定时清理、部署阻断恢复 |
| `v1.3` | [`versions/v1.3/README.md`](versions/v1.3/README.md) | 图片预览、结构化加载反馈、慢请求监控与异常脱敏、HTTP/3 验证 |
| `v1.2` | [`versions/v1.2/README.md`](versions/v1.2/README.md) | 性能基线、跨境公网诊断、纯文档变更跳过部署规则 |
| `v1.1.0` | [`versions/v1.1/README.md`](versions/v1.1/README.md) | Post 多图上传、Family 发帖、QA 回答时间、GitHub Actions SSH 自动部署 |
| `v1.0.0` | [`versions/v1/README.md`](versions/v1/README.md) | 初始版本需求、设计、计划、测试、发布与复盘全套交付材料 |

## 公开边界

文档不得加入真实 `.env`、数据库备份、家庭数据、SSH 私钥、`signing.keystore`、`signing-key-info.txt`、完整 Android 签名 ZIP 或任何密码。APK/AAB 如需分发，应通过独立受控渠道提供，不与公开源代码和文档混放。
