# EiheiZone V1 交付材料

## 交付说明

本目录是 EiheiZone V1 的公开文档交付包，汇总从需求定义到部署发布的正式成果。应用源代码、数据库迁移、自动化测试和部署配置由 EiheiZone 应用仓库管理，不在本目录重复复制。

V1 于 2026-08-05 完成最终验收，发布结论为 **Accept**，适用于家庭小范围使用、项目复盘和作品集展示。

## 材料目录

| 文件                      | 内容                       | 状态        |
| ----------------------- | ------------------------ | --------- |
| `00a_v1_technology_stack.md` | 最终技术栈、职责、安全及运行基线       | Accept    |
| `00b_v1_development_process.md` | 六阶段流程、阶段门禁及迭代规则       | Completed |
| `01_v1_requirements.md` | 产品目标、角色、范围、功能需求和验收标准     | Accept    |
| `02_v1_design.md`       | 总体架构、权限、数据、API、页面和部署边界   | Accept    |
| `03_v1_plan.md`         | 11 项开发任务、实施顺序和完成记录       | Completed |
| `04_v1_test_report.md`  | 功能追踪、权限验证、覆盖率和测试结论       | Accept    |
| `05_v1_release.md`      | 公网、PWA、Android、运维及风险接受记录 | Accept    |
| `06_v1_summary.md`      | V1 项目成果、过程复盘、关键取舍和后续方向   | Final     |

完整审阅时建议按编号顺序阅读：先了解技术与流程基线，再查看五个阶段的正式证据。只需快速了解项目时，可先阅读 `06_v1_summary.md`，再按需查阅对应阶段文档。

## 对应工程产物

- FastAPI、Next.js 与 PostgreSQL 应用代码；
- Alembic 数据库迁移；
- Pytest、Vitest 和 Playwright 自动化测试；
- Docker Compose、Caddy 和环境变量模板；
- PWA Manifest、图标和公开截图。

## 公开边界

本交付包不得加入真实 `.env`、数据库备份、家庭数据、SSH 私钥、`signing.keystore`、`signing-key-info.txt`、完整 Android 签名 ZIP 或任何密码。APK/AAB 如需分发，应通过独立的受控渠道提供，不与公开源代码和文档混放。
