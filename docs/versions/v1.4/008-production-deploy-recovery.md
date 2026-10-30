# V1.4 / 008：生产部署阻断恢复与发布链路硬化

| 目标版本 | `v1.4` |
| --- | --- |
| 状态 | Accepted |
| 日期 | 2026-10-29 |
| 分支 | `fix/v1.4-008-production-deploy-recovery` |

## 1. 目标

恢复生产发布到 GitHub `main` 的自动链路，完成 `f2f1b2b` 的部署，并让部署失败时直接显示服务器工作树漂移信息。

## 2. 故障证据

- 本地与 GitHub `main` 的目标提交为 `f2f1b2b8e9555ff15914a60a0c04e6cb2142a78f`，对应 CI 成功。
- GitHub Deploy 运行 `40813555125`（`f2f1b2b`）失败；`abfe065` 对应的 Deploy 运行也失败。
- 服务器 `/opt/eiheizone` 仍在 `44b5d77e17fdc85b3384134b4e4f6394861ee031`，`current-successful-commit` 与运行镜像均为该 SHA。
- 服务器 `backup-to-cos.sh` 存在未提交内容和权限变化。`deploy.sh` 在 fetch 前拒绝脏工作树，导致服务器无法同步最新提交。
- 服务器数据库迁移为 `e4f5a6b7c8d9`，Compose 服务没有 `media-cleanup-worker`。
- 公网健康接口返回 200，只能证明旧版本可用。

## 3. 修正方案

1. 在服务器受限备份目录保存 `git diff --binary`、状态文件、提交号、镜像标签、脚本模式和校验值。
2. 将服务器差异与 `abfe065` 及 `origin/main` 对照；若没有额外业务改动，再恢复到最新 `origin/main`，并保持仓库记录的文件权限。
3. 运行 `/opt/eiheizone/deploy.sh`，由脚本完成 fast-forward、SHA 镜像构建、Migration、Compose 更新和公网健康检查。
4. 验证目标提交、Migration、服务列表、镜像标签、健康接口和媒体清理 dry-run；需要账号的登录、图片编辑和通知烟测单独记录实际结果。
5. 在 `deploy.sh` 的脏工作区错误中输出 `git status --short`、未暂存差异摘要和暂存差异摘要；在运维手册中明确禁止直接修改服务器 Git 跟踪文件。

## 4. 验收标准

- [x] 服务器 `HEAD`、`.deploy/current-successful-commit`、backend/frontend 镜像标签均为 `f2f1b2b8e9555ff15914a60a0c04e6cb2142a78f`。
- [x] `/opt/eiheizone` 的 `git status --short` 为空。
- [x] Compose 包含并运行 `media-cleanup-worker`，backend/frontend/worker 正常。
- [x] Alembic 当前版本为 `f1a2b3c4d5e6`。
- [x] `https://eihei.zone/api/v1/health` 返回 `{"status":"ok"}`。
- [x] 媒体清理脚本 dry-run 成功，结果为 0 个孤立 Post 图片；未执行删除。
- [x] 登录、Post 图片编辑/读取和通知链路的人工烟测本轮不执行，用户已确认接受该边界。
- [x] `git diff --check` 与三份脚本的 `bash -n` 通过；Bash 检查通过服务器 Bash 读取标准输入完成。
- [x] 部署失败诊断会保存工作树、Compose、Migration 和容器日志。
- [x] 回滚在当前数据库 migration 与目标代码 head 不一致时安全拒绝，不执行逆向 Migration。

## 5. 实现与测试记录

| 检查 | 结果 | 说明 |
| --- | --- | --- |
| 本地文档与部署脚本修改 | Pass | 增加脏工作树诊断、运维说明和清理脚本 `PYTHONPATH` |
| 服务器差异留证 | Pass | `/var/backups/eiheizone/deploy-recovery-20261029` |
| 服务器差异审阅 | Pass | 仅有与 `abfe065`/`origin/main` 相同的备份脚本内容及文件模式差异 |
| 生产部署 | Pass | `deploy.sh` 成功发布 `f2f1b2b8e9555ff15914a60a0c04e6cb2142a78f` |
| 生产验收 | Pass | Compose、Migration、worker、公网健康和 dry-run 均通过 |
| 部署/回滚保护 | Pass | 已增加失败证据文件和 migration head 兼容性闸门 |

## 6. 遗留风险

- 当前工作区曾受 Codex 沙箱限制，经过受控 Git 元数据写入后已创建短期分支；本次仍未提交或改写 Git 历史。
- 本地部署脚本诊断、回滚闸门和文档修正尚未提交到 GitHub，因此不会影响本次已完成的生产发布；后续合并前应在 CI 中验证。
- GitHub 原始失败日志未直接下载；阻断原因已由服务器工作树状态和 `deploy.sh` 守卫交叉确认，后续失败可由新增诊断文件留证。
- 数据库 Migration 不执行逆向回滚；新增 migration head 闸门会阻止不兼容回滚，跨 migration 恢复仍需单独备份和兼容性方案。
