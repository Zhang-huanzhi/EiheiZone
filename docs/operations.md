# 当前运维基线

| 适用产品版本 | Current / v1.1.x |
| --- | --- |
| 文档状态 | Active |
| 最后更新 | 2026-08-15 |

本文档记录当前安全运维、自动发布和恢复边界。`v1.0.0` 的完整发布事实保存在 [`versions/v1/05_v1_release.md`](versions/v1/05_v1_release.md)，v1.1 自动发布链路的建立与演练证据保存在 [`versions/v1.1/003_github_ssh_cicd.md`](versions/v1.1/003_github_ssh_cicd.md)。

## 1. 环境与持久化边界

- 本地开发使用独立开发数据库；自动化测试使用独立测试数据库和虚构数据；
- 生产服务器目录固定为 `/opt/eiheizone`，由 Docker Compose 运行 PostgreSQL、FastAPI、Next.js 和 Caddy；
- Caddy 是唯一公开入口，PostgreSQL、FastAPI 和 Next.js 只连接内部 Compose 网络；
- `/opt/eiheizone/.env`、`.deploy/` 和 Docker volumes 是服务器状态，不提交到 Git；
- `postgres_data` 保存数据库，`media_data` 保存 Post 图片，`caddy_data`/`caddy_config` 保存 Caddy 状态。

生产配置只存在于 VPS 的受限环境文件中。GitHub Secrets 只保存 SSH 连接所需的 `SSH_HOST`、`SSH_PORT`、`SSH_USER`、`SSH_PRIVATE_KEY` 和可信 `SSH_KNOWN_HOSTS`，workflow 不生成或覆盖生产 `.env`。

## 2. CI 与自动部署

Pull Request 和 `main` push 会运行 CI：

| Job | 检查 |
| --- | --- |
| Backend | PostgreSQL 17、锁定依赖、Ruff、Alembic upgrade、pytest |
| Frontend | 锁定依赖、ESLint、Vitest、TypeScript、Next.js production build |
| Deployment artifacts | Bash 语法、Compose 配置、前后端生产镜像构建 |

`main` push 的 CI 成功后，Deploy workflow 进入 `production` Environment，通过固定 host key 的 SSH 连接调用：

```bash
bash /opt/eiheizone/deploy.sh
```

`deploy.sh` 拒绝脏工作区和并发部署，只允许 fast-forward 到 `origin/main`，用完整 commit SHA 标记镜像，执行 Compose 更新，再验证容器就绪和 `https://eihei.zone/api/v1/health`。成功后写入：

```text
/opt/eiheizone/.deploy/current-successful-commit
/opt/eiheizone/.deploy/previous-successful-commit
```

## 3. 发布检查

1. Pull Request required checks 全部成功并合并到 `main`；
2. Production Deploy workflow 成功，记录完整 commit SHA；
3. 验证健康接口、HTTPS、登录、公开与家庭内容权限；
4. 涉及 Post 图片时验证上传、显示、公开/家庭读取和 `media_data` 可写；
5. 涉及 QA 时验证 Family 与 Owner 的提问路由、回答和回答时间；
6. 只有上述结果均通过，才在该提交创建产品 tag 和 GitHub Release。

## 4. 常用检查

在生产目录执行：

```bash
cd /opt/eiheizone
sudo docker compose ps
sudo docker compose logs --tail=100 backend
sudo docker compose logs --tail=100 frontend
sudo docker compose logs --tail=100 caddy
curl --fail --show-error https://eihei.zone/api/v1/health
```

不要用无范围的 `docker compose restart` 代替故障分析；需要重启时明确指定服务，并在之后重新检查依赖服务和公网健康接口。

## 5. Migration 与回滚

FastAPI 容器启动前执行 `alembic upgrade head`。新 Migration 必须先在专用测试数据库验证升级；涉及不兼容数据变化时，必须另行设计双阶段发布、备份和恢复方案。

默认回滚到上一稳定 commit：

```bash
bash /opt/eiheizone/rollback.sh
```

也可以指定属于 `origin/main` 历史的完整 40 位 commit SHA：

```bash
bash /opt/eiheizone/rollback.sh <40-character-commit-sha>
```

部署与回滚共享 `/opt/eiheizone/.deploy/deploy.lock`。回滚优先复用目标 SHA 的镜像，并重新执行 Compose 和公网健康检查；它不会逆向执行 Alembic Migration，也不会删除 named volumes。数据库不兼容时必须人工评估，不能只依赖应用镜像回滚。

## 6. Post 图片维护

图片文件只能通过 FastAPI 鉴权接口读取，不直接公开 `media_data`。删除 Post 时会删除图片记录并尝试删除物理文件；上传超过 24 小时仍未绑定的 `pending` 图片，以及此前删除失败的 `cleanup_pending` 图片，按需执行：

```bash
cd /opt/eiheizone
sudo docker compose exec backend python scripts/cleanup_post_images.py
```

脚本不会清理已经绑定的 `attached` 图片。运行后记录删除数量，并抽查 Post 图片仍可访问；在没有独立媒体备份前，不直接进入 volume 手工批量删除文件。

## 7. 备份与秘密

named volume 只能覆盖容器重建和正常重启，不能覆盖 VPS 整机损坏、误删或磁盘不可用。可恢复备份至少必须成对覆盖 PostgreSQL 与 `media_data`，并通过隔离环境的恢复演练证明数据库记录与图片文件一致；异机加密备份和定期恢复演练当前仍未完成。

不得提交 `.env`、SSH 私钥、PEM、`signing.keystore`、签名密码、数据库备份、媒体卷副本或真实家庭数据。公开文档只记录管理原则、非敏感路径和验证结果。
