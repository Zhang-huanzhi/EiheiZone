# EiheiZone 文档

本目录保存 EiheiZone 的正式项目文档。当前文档描述现行系统与工作方式，版本目录保存已经验收并冻结的历史事实；源代码、Migration、自动化测试和部署配置仍以仓库实现为准。

## 文档分层

| 路径 | 职责 | 生命周期 |
| --- | --- | --- |
| `development-process.md` | 当前迭代、分支、测试、归档和发布流程 | 持续更新 |
| `architecture.md` | 当前系统职责、权限和运行边界摘要 | 持续更新 |
| `operations.md` | 当前 CI/CD、部署、Migration、备份和恢复基线 | 持续更新 |
| `versions/v1/` | `v1.0.0` 的完整历史交付材料 | Frozen |
| `versions/v1.1/` | `v1.1.0` 的五次迭代、发布摘要和验证记录 | Frozen |
| `iterations/` | 尚未归档版本的活动迭代记录与模板 | 随迭代更新 |
| `adr/` | 影响多个模块或未来演进的架构决策 | 按需新增 |

产品版本使用 `v1.0.0`、`v1.1.0` 等 Git tag。活动迭代在 `iterations/v1.x/` 中积累；版本验收时，将整组记录移动到 `versions/v1.x/`，补充版本 README，并在合并、CI 和生产验证成功后创建 tag 与 GitHub Release。

## 阅读入口

- 初次了解项目：阅读仓库根目录对应语言的 README；
- 了解当前怎么开发和发布：阅读 [`development-process.md`](development-process.md)；
- 了解当前系统：阅读 [`architecture.md`](architecture.md)；
- 了解部署、回滚和数据边界：阅读 [`operations.md`](operations.md)；
- 审阅 `v1.0.0`：阅读 [`versions/v1/README.md`](versions/v1/README.md)；
- 审阅 `v1.1.0`：阅读 [`versions/v1.1/README.md`](versions/v1.1/README.md)；
- 了解正在进行的后续工作：阅读 [`iterations/README.md`](iterations/README.md) 和对应活动版本目录。

## 公开边界

文档不得加入真实 `.env`、数据库备份、家庭数据、SSH 私钥、`signing.keystore`、`signing-key-info.txt`、完整 Android 签名 ZIP 或任何密码。APK/AAB 如需分发，应通过独立的受控渠道提供，不与公开源代码和文档混放。
