# EiheiZone v1.2 历史交付

| 产品版本 | `v1.2` |
| --- | --- |
| 状态 | Accepted / Archived |
| 归档范围 | 性能基线、公网访问诊断、纯文档变更部署规则 |

本目录归档 v1.2 的三次迭代记录。原活动目录已整体移动到这里，包含公网诊断所需的原始记录和图片附件；文件内部相对链接保持不变。

## 版本内容

| 顺序 | 迭代 | 主要结果 |
| --- | --- | --- |
| 001 | [`001_performance-baseline.md`](001_performance-baseline.md) | 建立浏览器端到端、API、页面 HTML 和服务器资源性能基线，定位跨境公网路径为主要长尾因素。 |
| 002 | [`002_performance-diagnosis.md`](002-performance-diagnosis.md) | 通过 Ping、路由、浏览器 Protocol 和 TCP 检查进一步记录公网访问问题及可选缓解方案。 |
| 003 | [`003_docs-only-deploy.md`](003_docs-only-deploy.md) | 配置纯 `docs/**` 合并后的 CI/CD 触发边界，保留 Pull Request required checks。 |

## 验收与未验证项

- 001 的本地性能基线和资源诊断记录已归档，生产环境无业务写入、Migration、重启或部署变更。
- 002 的网络诊断材料已归档，结论仅用于方向判断，不将 Cloudflare 或 BBR 的效果写成已证明的性能收益。
- 003 已按本次归档要求标记为 `Accepted`，YAML 结构和 required jobs 的静态检查记录为通过。
- 003 的真实 GitHub Pull Request、合并后 `main` CI 和 Deploy 触发行为仍需维护者在线验证；本归档不虚构该证据。

## 发布记录

本归档不执行 Git 分支、提交、推送、合并或产品 tag 操作。后续如创建正式产品 tag，应在维护者完成在线验证并确认生产发布链路后回填。

## 遗留风险

- 跨境公网链路仍可能造成高 RTT、丢包和页面长尾；EdgeOne、源站地域和静态资源 CDN 仍是后续评估项。
- GitHub 路径过滤的真实行为需要后续纯文档 Pull Request 和混合变更 Pull Request 验证。
