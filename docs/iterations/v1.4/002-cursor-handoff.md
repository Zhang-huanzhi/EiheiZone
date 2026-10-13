# V1.4 / 002 Codex 到 Cursor 交接

| 项目 | 内容 |
| --- | --- |
| 目标版本 | `v1.4` |
| 状态 | Accepted |
| 日期 | 2026-10-13 |
| 分支 | `docs/v1.4-002-cursor-handoff` |

## 前言

微信测试号通知 PoC 已提前合并到 `main`。继续做该功能时另开 `feat/` 分支，不在本分支上延续。本次只处理从 Codex 切换到 Cursor 的协作约定。

## 1. 目标

让仓库内的协作说明可以被 Cursor 直接读取，并且不再依赖 Codex 专用路径。本机服务器连接参数继续只留在本机，不进入后续提交。

## 2. 本次范围

- 从 `main` 建立独立分支 `docs/v1.4-002-cursor-handoff`。
- 新增本迭代文档，并登记到 v1.4 活动迭代入口。
- 将仓库根目录 `AGENTS.md` 改为可跟踪文件，补上原先只写在上一级工作区说明里的沟通规则。
- 本机登录说明从 `.codex/server-login.local.md` 移到 `.local/server-login.md`。
- 停止跟踪该登录说明，并在 `.gitignore` 中忽略 `.local/` 与 `.codex/`。
- 把两份 `AGENTS.md` 里的 Git 约定从「禁止执行」改为「可以执行，但一次功能只使用一条分支」。

## 3. 不做事项

- 不修改应用代码、API、数据库、Migration、CI workflow 或部署脚本。
- 不修改 `001-wechat-test-notifications.md`。
- 不把 `~/.codex/config.toml`、命令放行规则、模型或代理配置抄进仓库。
- 不新建与 `AGENTS.md` 平行的 `.cursor/rules`。
- 不改写已经冻结的版本文档。
- 不清理 Git 历史中已经存在的登录说明。
- 不在本迭代继续微信通知功能。

## 4. 技术方案与候选选择

Cursor 已经读取仓库根目录 `AGENTS.md`，因此协作约定继续放在这个文件里，不另建一套 Cursor 规则。原先 `.gitignore` 排除了 `/AGENTS.md`，换一台机器或重新克隆后 Cursor 看不到这些约定。该文件没有主机、密钥或密码，本次改为随仓库保存。

服务器登录说明只含本机连接参数，继续不提交。路径改为 `.local/server-login.md`，避免目录名绑定 Codex。`.gitignore` 同时忽略 `.codex/`，避免以后把旧目录重新加进来。

上一级 `EiheiZone/AGENTS.md` 仍负责 `notes/` 与代码目录的工作区边界。代码仓库自己的 `AGENTS.md` 补上中文回答、先说明范围、以及只做解释时不改文件这三条，这样只克隆本仓库时也有同样的沟通约定。

仓库和上一级工作区的 `AGENTS.md` 都允许执行 Git。一次功能或一次迭代只开一条短期分支，后续修改留在这条分支上；提交、推送、Pull Request 和合并仍要用户明确提出。上一级目录和 `notes/` 仍不主动提交。这项长期约定记录在 [ADR-0001](../../adr/0001-coding-agent-collaboration.md)。

## 5. 影响范围

- 合并到 `main` 时，变更包含 `AGENTS.md` 和 `.gitignore`，不属于纯 `docs/**` 推送，会按现有规则运行 CI，并在 CI 成功后进入生产部署。
- 生产运行内容不依赖这两个文件。
- 登录说明已在 `0fc51b6` 进入过仓库。本次只让它从后续提交中消失，旧提交里仍然有该文件。

## 6. 验收标准

1. 分支 `docs/v1.4-002-cursor-handoff` 从当前 `main` 分出。
2. 本文件存在，并且 v1.4 入口能链接到它。
3. `AGENTS.md` 不再被 Git 忽略，服务器连接说明指向 `.local/server-login.md`。
4. `.local/server-login.md` 只存在于本机，`git status` 不把它列为待提交文件。
5. `.codex/server-login.local.md` 从后续提交的跟踪清单中移除。
6. 产品代码、001 迭代文档和冻结版本文档没有被修改。
7. 两份 `AGENTS.md` 都写明可以执行 Git，并且同一次功能只使用一条分支。

## 7. 实现与测试记录

| 检查 | 结果 | 证据 |
| --- | --- | --- |
| 建立分支 | 已完成本地分支 | `docs/v1.4-002-cursor-handoff` |
| 独立迭代文档与入口 | 已写入 | 本文件；`docs/iterations/v1.4/README.md` |
| `AGENTS.md` 可跟踪 | 待提交时核对 | 已去掉 `/AGENTS.md` 忽略规则，并补上沟通约定 |
| Git 约定 | 已改写 | 仓库与上一级 `AGENTS.md`：可以执行 Git，一次功能一条分支 |
| ADR | 已写入 | [ADR-0001](../../adr/0001-coding-agent-collaboration.md)，状态 Accepted |
| 登录说明移到本机路径 | 已在本机移动 | `.local/server-login.md`；`.codex/` 目录已删除 |
| 停止跟踪登录说明 | 已暂存删除 | `git rm --cached -- .codex/server-login.local.md` |
| 应用测试、Lint、构建 | 未运行 | 本次没有改应用代码 |
| 验收 | Accepted | 用户于 2026-10-13 验收 |

## 8. 遗留风险

- 历史提交 `0fc51b6` 仍包含旧的登录说明。需要从历史中移除时，应单独决定，并相应更新已经推送的远程历史。
- 用户目录中的 Codex 模型、代理、沙箱和命令放行规则不会自动带到 Cursor。
- 工作区现已同时包含上一级 `EiheiZone` 与 `eiheizone`。
- 变更尚未提交，也尚未通过 Pull Request。
