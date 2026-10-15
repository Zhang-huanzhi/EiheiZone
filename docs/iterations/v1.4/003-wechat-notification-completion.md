# V1.4 / 003 微信测试号通知完善与联调准备

| 项目 | 内容 |
| --- | --- |
| 目标版本 | `v1.4` |
| 状态 | In Progress |
| 日期 | 2026-10-15 |
| 分支 | `feat/v1.4-003-wechat-notification-completion` |

## 前言

[`001-wechat-test-notifications.md`](001-wechat-test-notifications.md) 已将微信测试号通知 PoC 的基础结构提前合入 `main`，但仍存在 PostgreSQL 下 `due_outbox` 外连接锁查询报错、OpenID 换绑未先 `flush` 触发唯一约束冲突、重复事件入队未幂等去重、前后端自动化测试未补齐，以及生产环境和测试号后台尚未完成配置联调等问题。本迭代在独立分支上完成上述缺陷修复、消息格式调整、测试补齐与联调准备。

## 1. 目标

完成微信测试号通知服务的缺陷修复、无跳转链接模板消息调整与前后端自动化测试覆盖，并配合微信测试号管理网页完成服务器配置与真实通知链路联调。

## 2. 本次范围

- 修复 `due_outbox` 在 PostgreSQL 下因 `joinedload` 左外连接配合 `FOR UPDATE SKIP LOCKED` 抛出的 `FeatureNotSupported` 错误，改为 `selectinload` 仅锁定 `notification_outbox` 行；
- 修复 `bind_open_id_by_code` 在同一 OpenID 换绑到另一账号时未先 `flush` 删除旧记录导致的唯一约束冲突；
- 补齐 `add_outbox` 幂等检查，确保同一会话或数据库中重复触发相同 `(event_type, aggregate_id, recipient_user_id, channel)` 不会重复入队或抛出冲突；
- 收紧收件人有效性与角色校验（仅 `ACTIVE` 状态的 `FAMILY` / `OWNER` 账号入队及投递），补齐永久失败时的结构化错误日志；
- 调整微信模板消息载荷：去掉模板消息中的 `url` 跳转链接（因有状态登录 Cookie 绑定在父母常用浏览器/桌面图标中，微信内置浏览器无登录态），仅发送事件摘要与打开常用浏览器的提示，并在发送报微信错误码时清理本地缓存的 `access_token`；
- 回调 XML 解析遇到非法 XML 时返回 `400 WECHAT_XML_INVALID`，被动回复填充真实时间戳；
- 补齐后端 Migration 升降级测试、通知服务/回调/Worker 全链路测试、权限边界测试及前端 Vitest 组件与 API 测试；
- 对齐生产服务器 Git 工作区状态，准备微信测试号网页接入校验与模板配置。

## 3. 不做事项

- 不在微信模板消息中附带网页跳转 URL，也不开发微信网页授权免登；
- 不发送 Post 或 QA 正文、图片及家庭敏感数据；
- 不新增数据库表或修改现有 `d7a1c2e3f4b5` Migration 表结构；
- 不将微信测试号承诺为长期正式生产通知渠道。

## 4. 技术方案与候选选择

1. **去除模板消息跳转 URL**：网站采用服务端 Session + `HttpOnly` Cookie 的有状态登录，父母通常在手机系统浏览器或添加到主屏幕的入口中保持登录态。若在微信模板消息中传入 `url`，点击卡片会强制在微信内置 WebView 中打开并要求重新登录。因此去掉 `url` 字段，仅通过模板卡片展示“有新的家庭近况 / 有新的家庭问题 / 你的问题有新回复”摘要与“请打开常用浏览器查看详情”提示。
2. **PostgreSQL 行锁与预加载**：PostgreSQL 不允许对 `LEFT OUTER JOIN` 的可空侧使用 `FOR UPDATE`。`due_outbox` 改用 `selectinload(NotificationOutbox.recipient)`，主查询只锁定 `notification_outbox` 待处理记录，既解决 PostgreSQL 报错，也避免无谓锁定 `users` 表记录。
3. **幂等入队与换绑事务顺序**：`add_outbox` 先检查当前 Session 新增对象与数据库已有记录，存在则直接复用；`bind_open_id_by_code` 在删除旧的同 `open_id` 绑定后立即 `db.flush()`，再插入或更新当前用户的绑定记录。

## 5. 影响范围

- 后端：`backend/app/core/config.py`、`backend/app/modules/notifications/{repository,service,wechat,worker}.py`、`backend/.env.example`、`deploy.env.example`；
- 测试：`backend/tests/notifications/{test_wechat,test_notification_migration}.py`、`backend/tests/integration/test_api_permissions.py`、`frontend/src/features/notifications/{notification-api.test.ts,notification-settings.test.tsx}`；
- 文档：`docs/iterations/v1.4/{README,001-wechat-test-notifications,003-wechat-notification-completion}.md`。

## 6. 验收标准

1. `due_outbox` 与 `process_once` 在真实 PostgreSQL 测试库下正常加锁拉取、投递、退避重试并在超过上限时记录永久失败结构化日志。
2. 同一微信 `open_id` 从账号 A 换绑到账号 B 时事务正常提交，不触发唯一约束异常。
3. 重复入队同一事件不会产生重复 Outbox 记录或引发事务失败；非 `active` 状态的账号不会入队或投递。
4. 微信模板消息请求载荷不包含 `url` 字段，且发送返回非 0 `errcode` 时自动清空缓存的 `access_token`。
5. 前后端 Lint、TypeScript 类型检查、Vitest 与 Pytest（含通知 Migration 往返测试）全部通过。
6. 生产服务器配置微信测试号 `WECHAT_APP_ID`、`WECHAT_APP_SECRET`、`WECHAT_TOKEN`、`WECHAT_TEMPLATE_ID` 并开启 `WECHAT_NOTIFICATIONS_ENABLED=true` 后，测试号 URL 接入校验、扫码关注、发送绑定码绑定及新建 QA/回答/新建 Post 微信通知真实送达。

## 7. 实现与测试记录

| 检查 | 结果 | 证据 |
| --- | --- | --- |
| 后端 Ruff 检查 | PASS | `ruff check app tests` 全部通过 |
| 后端通知与 Migration 测试 | PASS | `pytest` 全量 260 passed（含新增 `test_notification_migration.py` 与 `test_wechat.py` 10 项测试） |
| 后端权限与契约集成测试 | PASS | `pytest tests/integration` 30 passed |
| 前端 ESLint、Vitest、TypeScript | PASS | 34 test files / 103 tests passed（含新增 `notification-api.test.ts`、`notification-settings.test.tsx`）；`tsc --noEmit` 通过 |
| 生产服务器 Git 状态对齐 | 已完成 | `/opt/eiheizone` 已对齐至 `origin/main`（`65a283e`），消除强推导致的 fast-forward 阻塞 |
| 生产环境写入 `WECHAT_TOKEN` 并重建当前 backend 镜像 | 已完成 | 未走 PR/CD；使用正在运行的镜像 `8486b0ae` 重建 backend。公网签名校验返回 `echostr`，错误签名返回 403 |
| 微信测试号 URL 接入校验 | 已通过 | 测试号页面已保存回调 URL；backend 日志中微信 GET `/api/v1/wechat/callback` 返回 200。凭据不写入本文档 |
| 测试模板与凭据 | 已写入服务器 | 模板标题「家庭网站通知」，正文占位符为 `keyword1` / `keyword2`。AppID、AppSecret、Token、模板 ID 已写入生产 `.env`，`WECHAT_NOTIFICATIONS_ENABLED=true`。微信 `access_token` 获取成功。凭据不写入本文档 |
| 当前镜像的 Outbox 查询 | 已在运行中的 worker 容器热修复 | 旧镜像的 `joinedload` + `FOR UPDATE` 会报错。已把本地修复后的 `repository.py` 放进正在运行的 worker 容器并重启。容器按旧镜像重建后，这个修复会消失，仍需随分支正式部署 |
| 真实微信送达 | 已收到，样式已调整 | 用户完成绑定并收到第一张模板卡片。微信不再展示 `first` / `remark`，旧卡片只剩日期和「详情」。已换成 `keyword1`（事项）和 `keyword2`（上海时间），并不再附带跳转链接。已向已绑定微信号发送一张「通知样式已更新」预览 |
| 当前镜像的发送代码 | 仅存在于运行中的 worker 容器 | 样式修改和 Outbox 查询修复都在容器内。按旧镜像重建 worker 后会恢复成难看的旧卡片，仍需随分支正式部署 |

## 8. 遗留风险

- 本迭代保持 In Progress。001 已于 2026-10-15 按绑定、新建问题和首次回答的真实送达验收。
- 修复代码还在本分支，线上 worker 只是临时放入了修复文件。按旧镜像重建后，Outbox 查询错误和带链接的旧卡片会回来。
- 新建近况的微信送达还没有做人工验收。
- 微信卡片目前只显示标题和日期，事项正文没有显示出来。样式留到后续迭代。
- 微信测试号最多支持 100 名关注者，且无商业 SLA，仅用于家庭内部 PoC 验证。
