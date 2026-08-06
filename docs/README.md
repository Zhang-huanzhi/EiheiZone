# EiheiZone 文档

本目录是 EiheiZone 的正式项目文档。应用源代码、数据库迁移、自动化测试和部署配置由仓库本身管理，不在文档中重复复制。

## 文档分层

| 路径 | 职责 | 生命周期 |
| --- | --- | --- |
| `development-process.md` | 当前开发、分支、测试、合并和发布流程 | 持续更新 |
| `architecture.md` | 当前系统职责和边界摘要 | 持续更新 |
| `operations.md` | 当前部署、Migration、备份和恢复基线 | 持续更新 |
| `versions/v1/` | V1 的完整历史交付材料 | Frozen |
| `iterations/` | V1.1、V1.2 等后续迭代记录 | 每次迭代新增或更新 |
| `adr/` | 影响多个模块或未来演进的架构决策 | 按需新增 |

产品版本使用 `v1.0.0`、`v1.1.0` 等 Git tag 表示；文档不再单独维护需要与产品版本保持一致的手工版本号。文档自身使用状态和最后更新时间表达当前有效性。

## 阅读入口

- 初次了解项目：阅读仓库根目录的 README；
- 了解当前怎么开发：阅读 `development-process.md`；
- 了解当前系统：阅读 `architecture.md`；
- 了解部署和恢复边界：阅读 `operations.md`；
- 审阅 V1 交付：阅读 `versions/v1/README.md`；
- 了解一次后续变更：阅读对应的 `iterations/` 文档。

## 公开边界

文档不得加入真实 `.env`、数据库备份、家庭数据、SSH 私钥、`signing.keystore`、`signing-key-info.txt`、完整 Android 签名 ZIP 或任何密码。APK/AAB 如需分发，应通过独立的受控渠道提供，不与公开源代码和文档混放。
