# 当前运维基线

| 适用产品版本 | Current / v1.x |
| --- | --- |
| 文档状态 | Active |
| 最后更新 | 2026-08-06 |

本文档记录当前的安全运维边界和常用操作。V1 的完整部署、PWA、Android、风险接受和验收事实保存在 [`versions/v1/05_v1_release.md`](versions/v1/05_v1_release.md)。

## 1. 环境边界

- 本地开发使用独立开发数据库；自动化测试使用独立测试数据库和虚构数据；
- 生产由 Docker Compose 运行 PostgreSQL、FastAPI、Next.js 和 Caddy；
- 生产配置只存在于 VPS 的受限环境文件中；
- PostgreSQL 不直接暴露公网，Caddy 是唯一公开入口。

## 2. 发布顺序

1. 在本地完成受影响的后端测试、前端测试、Lint、类型检查和生产构建；
2. 涉及数据库变化时，在测试数据库执行并验证新的 Alembic Migration；
3. 发布前确认生产数据库有可恢复的备份或明确记录当前备份风险；
4. 从已合并的产品 tag 部署应用并执行 Compose 更新；
5. 验证健康接口、HTTPS、登录和受影响的核心流程；
6. 在迭代文档中记录 tag、commit、Migration、部署时间和异常。

## 3. 常用检查

在生产目录执行：

```bash
sudo docker compose ps
sudo docker compose logs --tail=100 backend
sudo docker compose logs --tail=100 frontend
sudo docker compose logs --tail=100 caddy
sudo docker compose restart
```

涉及 Migration 时，不在生产数据库尝试实验性降级；先在临时数据库验证升级、降级和重新升级行为。

## 4. 备份与秘密

当前 named volume 可以覆盖容器重建和正常重启，但不能覆盖 VPS 整机损坏、误删或磁盘不可用。异机加密备份和恢复演练仍属于后续运维事项。

不得提交 `.env`、SSH 私钥、PEM、`signing.keystore`、签名密码、数据库备份或真实家庭数据。公开文档只记录管理原则和非敏感校验信息。
