# EiheiZone v1.4 历史交付

| 产品版本 | `v1.4` |
| --- | --- |
| 状态 | Accepted / Archived（含延期项） |
| 归档日期 | 2026-10-30 |
| 延期项 | 006 COS 基础数据防灾 |

本目录归档 v1.4 已完成的八次迭代中的七次。006 已转入 [`../../iterations/backlog/006-basic-disaster-recovery.md`](../../iterations/backlog/006-basic-disaster-recovery.md)，不作为本版本已完成能力声明。

## 版本内容

| 编号 | 迭代 | 结果 |
| --- | --- | --- |
| 001 | [微信测试号通知 PoC](001-wechat-test-notifications.md) | Accepted：绑定、Outbox 和基础通知链路完成。 |
| 002 | [Codex 到 Cursor 交接](002-cursor-handoff.md) | Accepted：仓库协作和单分支规则落地。 |
| 003 | [微信测试号通知完善](003-wechat-notification-completion.md) | Accepted：Post/QA 通知、重试、幂等和真实送达完成。 |
| 004 | [Post 评论](004-post-comments.md) | Accepted：扁平文本评论、权限和级联删除完成。 |
| 005 | [微信绑定码状态约束](005-wechat-bound-code.md) | Accepted：已绑定用户不能重复生成绑定码。 |
| 007 | [Post 图片编辑与媒体清理](007-post-image-edit-cleanup.md) | Accepted：图片编辑和清理 worker 完成。 |
| 008 | [生产部署阻断恢复](008-production-deploy-recovery.md) | Accepted：部署诊断、恢复和 Migration 回滚闸门完成。 |

## 验收与边界

- 007 引入 Migration `f1a2b3c4d5e6`；当前代码和生产记录以实际 Migration head 为准。
- 008 的生产部署、Compose 服务、公网健康检查和故障证据均已记录；未在本文重新声称未执行的登录或图片人工烟测。
- 006 已完成脚本模拟、COS 虚构文件验证和隔离恢复演练，但每日 cron 尚未安装，不能视为持续运行的正式备份服务。
- 本归档不创建产品 tag、Release 或提交；这些动作须在归档 PR、CI、部署和生产验收完成后由维护者明确执行。

## 遗留风险

- COS 与 VPS 同属腾讯云，不能覆盖云账号或平台级故障。
- 备份失败目前依靠日志人工发现，尚未配置自动告警。
- 006 后续继续实施时，应新建 v1.5.x 迭代和新分支，不恢复已归档分支继续堆叠。
