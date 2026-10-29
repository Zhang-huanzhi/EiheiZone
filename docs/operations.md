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

所有 Pull Request 都会运行 CI。`main` push 仅在变更包含 `docs/**` 之外的路径时运行 CI；纯 `docs/**` 变更合并后跳过 CI，也不会触发后续生产部署：

| Job | 检查 |
| --- | --- |
| Backend | PostgreSQL 17、锁定依赖、Ruff、Alembic upgrade、pytest |
| Frontend | 锁定依赖、ESLint、Vitest、TypeScript、Next.js production build |
| Deployment artifacts | Bash 语法、Compose 配置、前后端生产镜像构建 |

需要运行 CI 的 `main` push 在 CI 成功后，由 Deploy workflow 进入 `production` Environment，通过固定 host key 的 SSH 连接调用：

```bash
bash /opt/eiheizone/deploy.sh
```

`deploy.sh` 拒绝脏工作区和并发部署，只允许 fast-forward 到 `origin/main`，用完整 commit SHA 标记镜像，执行 Compose 更新，再验证容器就绪和 `https://eihei.zone/api/v1/health`。成功后写入：

```text
/opt/eiheizone/.deploy/current-successful-commit
/opt/eiheizone/.deploy/previous-successful-commit
```

生产目录中的 Git 跟踪文件必须保持干净。不要直接在服务器上修改脚本、Compose 或应用源代码；运维修复应先提交到 GitHub `main`，再由部署脚本发布。若部署因脏工作区拒绝，脚本会输出 `git status --short` 以及暂存、未暂存差异摘要。先保存并审阅服务器差异，确认没有未纳入版本控制的业务改动后，才可以恢复到 `origin/main` 并重试部署。

部署失败时，脚本会把工作树状态、Compose 状态、当前 Alembic migration 和最近容器日志写入 `/opt/eiheizone/.deploy/failure-*.log`。该文件只用于故障排查，包含生产日志，排查完成后按服务器日志保留策略处理。

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

回滚脚本会先读取当前数据库 migration 和目标提交镜像中的 migration head；两者不一致或无法读取时，脚本会恢复当前提交并拒绝回滚。这样可以避免应用代码回退后访问更新的数据库结构。需要跨 migration 回滚时，必须先完成备份、兼容性评审和单独的数据恢复方案。

## 6. Post 图片维护

图片文件只能通过 FastAPI 鉴权接口读取，不直接公开 `media_data`。删除 Post 时会删除图片记录并尝试删除物理文件；上传超过 24 小时仍未绑定的 `pending` 图片，以及此前删除失败的 `cleanup_pending` 图片，按需执行：

```bash
cd /opt/eiheizone
sudo docker compose exec backend env PYTHONPATH=/app python scripts/cleanup_post_images.py
```

脚本不会清理已经绑定的 `attached` 图片。运行后记录删除数量，并抽查 Post 图片仍可访问；在没有独立媒体备份前，不直接进入 volume 手工批量删除文件。

## 7. 备份与秘密

named volume 只能覆盖容器重建和正常重启，不能覆盖 VPS 整机损坏、误删或磁盘不可用。`backup-to-cos.sh` 每天将 PostgreSQL custom dump 与 `/app/media` 图片归档为一份备份，通过 rclone crypt 客户端加密后上传到腾讯云 COS，保留最近 7 份。脚本在本地快照期间短暂停止 backend；本地数据库和图片快照完成后先恢复 backend 并等待健康检查，再执行网络上传。

### 初始化 COS 备份

由账号持有人在腾讯云控制台完成以下准备：

1. 确认账号已启用按量计费并查看当前地域费用。创建首尔地域（`ap-seoul`）私有标准存储桶；存储桶名称需使用你在控制台选定的实际名称。
2. 创建专用 CAM 子用户和访问密钥，并将权限限制到该存储桶及备份前缀。权限需满足 rclone 对象列举、上传、下载、删除及必要的分段上传操作。不要把主账号密钥用于服务器。
3. 在 VPS 创建权限受限的配置目录，并用 rclone 交互式配置两个 remote。第一个 remote 命名为 `cos`，类型 `s3`，Provider 选择 `TencentCOS`，填写 CAM 访问密钥，region `ap-seoul`、endpoint `cos.ap-seoul.myqcloud.com`，ACL 设为 `private`；其他选项保留默认值。第二个 remote 命名为 `cos-crypt`，类型 `crypt`，Remote 填 `cos:<控制台桶名>/eiheizone-backups`，启用文件名和目录名加密，并生成新的强密码。将该密码另存于密码管理器。配置目录为 `0700`、配置文件为 `0600`；配置文件包含 COS 凭证和 rclone crypt 密码，禁止提交 Git。

   ```bash
   sudo install -d -m 700 /etc/rclone
   sudo rclone --config /etc/rclone/rclone.conf config
   sudo chmod 600 /etc/rclone/rclone.conf
   ```
4. 使用只含虚构内容的临时文件，通过 crypt remote 上传、下载并比较文件，然后删除 COS 上的临时对象。将 crypt 密码另行存入密码管理器；恢复时需要这份密码，丢失后无法解密备份。
5. 确认仓库部署到 `/opt/eiheizone` 后，创建本地目录并安装 root 定时任务：

   ```bash
   sudo install -d -m 700 /var/backups/eiheizone
   sudo crontab -e
   ```

   添加以下条目：

   ```cron
   CRON_TZ=Asia/Seoul
   0 3 * * * /bin/bash /opt/eiheizone/backup-to-cos.sh >> /var/log/eiheizone-backup.log 2>&1
   ```

首次正式执行前，以 root 手工运行一次 `/bin/bash /opt/eiheizone/backup-to-cos.sh`，确认 `docker compose ps` 显示 backend 健康、COS 中出现当日加密备份。脚本要求以能管理 Docker Compose 的用户运行；默认以 root 运行。快照完成后服务会先恢复，上传在服务健康后进行。恢复 backend 时使用 `docker compose up --no-recreate`，这样不会在缺少 `DEPLOY_IMAGE_TAG` 时把正在运行的镜像换成 `latest`。`cos` remote 需要 `no_check_bucket = true`，避免没有建桶权限的子用户在上传前尝试创建存储桶。上传或远端校验失败时，脚本返回非零并保留本地恢复材料；这些材料包含未加密数据库和图片，权限为 `0700`，应尽快排查上传并在确认远端备份安全后删除。上传和校验成功后本地材料会删除，再清理超出最近 7 份的旧对象。若清理失败，脚本返回失败但不会影响新备份。

通过下列命令人工检查最近日志与服务状态：

```bash
sudo tail -n 100 /var/log/eiheizone-backup.log
cd /opt/eiheizone
sudo docker compose ps
```

本迭代不配置自动告警；需定期确认日志存在成功记录且 COS 中有最近备份。COS 与 VPS 同属腾讯云，不能覆盖云账号或平台级故障；实际存储和恢复流量费用按腾讯云控制台与账单为准。

### 恢复到新 VPS

准备代码仓库、生产 `.env`、rclone 配置和 crypt 恢复密码。`.env`、COS 凭证和恢复密码必须分别保存在安全位置，不能只保存在故障 VPS 或同一个备份中。先准备新的空 PostgreSQL 数据库及 `media_data` volume；不得在恢复前启动会执行 Migration 的 backend。

以 root shell 操作恢复文件，避免备份内容被其他本机用户读取：

```bash
sudo -i
rclone --config /etc/rclone/rclone.conf copyto \
  'cos-crypt:eiheizone-backups/<backup-file>' /var/tmp/eiheizone-backup.tar.gz
install -d -m 700 /var/tmp/eiheizone-restore
tar -xzf /var/tmp/eiheizone-backup.tar.gz -C /var/tmp/eiheizone-restore
cd /var/tmp/eiheizone-restore
sha256sum -c SHA256SUMS
```

确认目标是新的空数据库后恢复：

```bash
cd /opt/eiheizone
docker compose up -d --wait db
docker compose exec -T db sh -ec 'pg_restore --no-owner -U "$POSTGRES_USER" -d "$POSTGRES_DB"' \
  < /var/tmp/eiheizone-restore/database.dump
docker compose run --rm --no-deps -T --entrypoint tar backend \
  -xzf - -C /app/media < /var/tmp/eiheizone-restore/media.tar.gz
docker compose up -d --wait
```

`pg_restore` 只可用于新的空数据库；不得对已有生产数据库执行。完整恢复后检查 `/api/v1/health`、登录、家庭内容和 Post 图片，再记录备份时间与验证结果。恢复演练应使用与生产隔离的 Compose 项目、数据库和 media volume；确认当前应用的 Alembic migration 可从备份状态升级。应用启动会自动执行 `alembic upgrade head`，不兼容 Migration 必须先制定单独恢复方案。

不得提交 `.env`、SSH 私钥、PEM、`signing.keystore`、签名密码、数据库备份、媒体卷副本或真实家庭数据。公开文档只记录管理原则、非敏感路径和验证结果。

### 媒体清理任务

生产 Compose 运行 `media-cleanup-worker`，默认每 7 天扫描超过 24 小时的 pending 图片、cleanup_pending 图片和媒体目录中的孤立文件。清理失败会记录在 `media_cleanup_runs`，并通过现有微信通知发送给活跃 Owner（当前为 `zzk`）。手工检查可运行：

```bash
docker compose run --rm --no-deps backend env PYTHONPATH=/app python scripts/cleanup_post_images.py --dry-run --scan-orphans
docker compose run --rm --no-deps backend env PYTHONPATH=/app python scripts/cleanup_post_images.py --scan-orphans --max-items 1000
docker compose logs --tail=100 media-cleanup-worker
```
