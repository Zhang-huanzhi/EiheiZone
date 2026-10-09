# EiheiZone v1.3 历史交付

| 产品版本 | `v1.3` |
| --- | --- |
| 状态 | Accepted / Archived |
| 归档范围 | 图片预览、加载反馈、请求监控安全与 HTTP/3 访问验证 |

本目录归档 v1.3 的五次迭代记录。活动目录已整体移动到这里，迭代文件名和文件内部相对链接保持不变。

## 版本内容

| 顺序 | 迭代 | 主要结果 |
| --- | --- | --- |
| 001 | [`001-post-image-preview.md`](001-post-image-preview.md) | 统一图片缩略图和全屏查看的 `object-contain` 策略，避免横图、竖图和超宽图被裁剪。 |
| 002 | [`002-structured-loading-feedback.md`](002-structured-loading-feedback.md) | 增加结构化骨架屏、站内导航进度条和慢网络提示，改善长 RTT 下的等待反馈。 |
| 003 | [`003-request-slow-monitoring.md`](003-request-slow-monitoring.md) | 增加可配置慢请求阈值、稳定异常分类和按请求聚合的数据库查询指标。 |
| 004 | [`004-request-monitoring-hardening.md`](004-request-monitoring-hardening.md) | 脱敏未处理异常日志，并用 PostgreSQL 集成测试验证查询计时和请求隔离。 |
| 005 | [`005-http3-performance-test.md`](005-http3-performance-test.md) | 增加 Caddy UDP `443` 映射并完成生产 HTTP/3 协商验证，同时保留 HTTP/2 回退。 |

## 验收与验证

- 001、002 的前端 Vitest、ESLint、TypeScript 和生产构建记录为通过；002 的真实弱网交互留待云上环境补验。
- 003、004 的请求监控聚焦测试和 Ruff 检查记录为通过；004 记录了当前运行环境中 4 个既有图片上传用例因临时目录权限无法完成 fixture setup 的限制。
- 005 的 Compose 结构、生产 UDP `443`、Caddy `h3` 宣告和浏览器曾出现 `h3` 请求均已验证；多数请求仍回退到 `h2`，每路径 20 次的页面长尾对比尚未完成。
- 本版本无数据库结构变化、Alembic Migration 或应用层 HTTP API 变化。

## 发布记录

本归档不执行 Git 分支、提交、推送、合并或产品 tag 操作。正式发布记录应由维护者在归档 PR 合并、CI、部署和生产验收完成后回填。

## 遗留风险

- 跨境 RTT、丢包、浏览器网络条件和运营商路径仍可能造成页面长尾；HTTP/3 的实际收益尚未通过固定条件的完整采样证明。
- 生产日志采集、保留和告警规则依赖部署环境，尚未在仓库中统一配置。
- PostgreSQL 集成测试依赖专用测试库；临时目录权限问题需要在具备完整测试环境的机器补跑全量验收。
