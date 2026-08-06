# EiheiZone V1 部署与发布记录

## 1. 文档信息

| 项目 | 内容 |
| --- | --- |
| 项目名称 | EiheiZone（Personal Family Portal） |
| 文档名称 | V1 部署发布与打包分发记录 |
| 项目阶段 | V1 部署发布 / 打包分发 |
| 文档版本 | v1.1 |
| 文档状态 | Accept |
| 创建日期 | 2026-08-03 |
| 更新日期 | 2026-08-05 |
| 维护者 | Eihei |
| 目标读者 | 项目开发者、未来维护者、作品集查看者、家庭使用者 |
| 发布结论 | Accept |
| 发布日期 | 2026-08-05 |
| 适用范围 | V1 公网部署、PWA 发布、Android APK 打包与家庭内分发 |

## 2. 文档结论

EiheiZone V1 第六阶段按以下优先级完成：

1. **公网 Web**：将 Next.js、FastAPI 和 PostgreSQL 部署到云服务器，通过域名和 HTTPS 提供服务；
2. **PWA**：在公网 Web 基础上提供浏览器安装入口；
3. **Android TWA**：使用 PWABuilder 在线生成 Android 包，并在目标真机验收。由于本次目标设备无法稳定启动在线 TWA，最终交付包采用本机临时调整的 WebView APK 兜底。

截至 2026-08-05：

| 判定项 | 最终结论 |
| --- | --- |
| V1 核心功能 | 已完成并通过第五阶段功能与权限测试 |
| 公网部署 | 已完成，生产站点可以访问 |
| 生产账号 | Owner、Family 均可登录并完成各自核心流程 |
| PWA | 已上线，父母安卓真机安装与启动验收通过 |
| Android APK | 已完成构建、签名和父母安卓真机验收 |
| VPS 恢复 | 整机关机、开机后服务自动恢复验证通过 |
| 生产依赖安全审计 | 仍有 3 个 high severity 告警；作为已知风险接受，转入后续维护 |
| 异机数据备份与恢复 | V1 暂缓；接受单机 named volume 无法覆盖整机损坏的风险 |
| V1 正式状态 | **Accept；第六阶段完成，可以交付** |

本文件同时记录部署和分发，不再拆分为两个交付文档。未在 V1 处理的项目已明确转入后续维护或 V1.1，不阻止本次家庭小范围交付。

## 3. 发布身份

| 项目 | 值 |
| --- | --- |
| 产品名称 | EiheiZone |
| Web 版本 | V1 |
| Android 版本 | `1.0.2.0` |
| Android `versionCode` | `3` |
| Android 包名 | `zone.eihei.app` |
| 发布日期 | 2026-08-05 |
| Git 分支 | `main` |
| Git 提交 | `7ca50cac37b619528605f8ee71a99b1fa1e2b22d` |
| Git 提交说明 | `feat: prepare V1 production release` |
| 生产主站 | `https://eihei.zone` |
| Family 启动地址 | `https://eihei.zone/family` |

本次 Git 提交包含生产 Compose、Caddy、后端镜像补充、PWA Manifest、应用图标、安装截图和 Digital Asset Links。真实 `.env`、SSH 私钥、APK 签名密钥和签名密码不在应用 Git 仓库中。

## 4. 公网部署

### 4.1 基础设施

| 项目    | 实际选择                                   |
| ----- | -------------------------------------- |
| 云服务   | 腾讯云轻量应用服务器                             |
| 账号与付款 | 腾讯云中国站账号，支付宝购买                         |
| 地域    | 首尔                                     |
| 操作系统  | Ubuntu 24.04 LTS                       |
| 起步规格  | 2 核 CPU、2 GB 内存、50 GB SSD、30 Mbps 峰值带宽 |
| 管理方式  | SSH；腾讯云免密终端作为备用入口                      |
| 应用目录  | `/opt/eiheizone`                       |
| 发布方式  | 手工发布，不启用 CI/CD                         |

V1 使用公有云 IaaS 单机方案，不使用 AWS、Cloudflare 代理、Terraform、Kubernetes、宝塔、托管数据库或镜像仓库。

### 4.2 生产拓扑

```text
用户浏览器 / PWA / Android APK
  -> https://eihei.zone
  -> 腾讯云首尔 VPS
  -> Caddy :80 / :443
      -> 普通页面 -> Next.js :3000
      -> /api/*  -> FastAPI :8000
                       -> PostgreSQL 17 :5432
```

Docker Compose 管理四个服务：

| 服务 | 职责 | 公网暴露 |
| --- | --- | --- |
| Caddy | HTTPS、证书续期、`www` 跳转和反向代理 | `80`、`443` |
| Next.js | 页面、交互和服务端渲染 | 否 |
| FastAPI | Session、权限、API 和业务规则 | 否 |
| PostgreSQL 17 | 生产数据 | 否 |

PostgreSQL 使用 Docker named volume `eiheizone_postgres_data` 持久化。该 Volume 可以防止容器重建时丢失数据，但不能防止 VPS 磁盘损坏、误删除或整机不可用。

### 4.3 域名和 HTTPS

- `http://eihei.zone` 自动跳转到 HTTPS；
- `https://eihei.zone` 是唯一主站；
- `https://www.eihei.zone` 永久跳转到主站；
- Caddy 自动申请并续期 HTTPS 证书；
- PostgreSQL、FastAPI 和 Next.js 容器端口不直接暴露到公网；
- 腾讯云防火墙开放 Web 所需的 `80/443`，SSH 使用已配置的管理端口和认证方式。

## 5. 部署产物

应用 Git 仓库中的生产文件：

| 文件 | 用途 |
| --- | --- |
| `docker-compose.yml` | 定义 PostgreSQL、FastAPI、Next.js、Caddy、内部网络、健康检查和 Volume |
| `Caddyfile` | HTTPS 主域名、`www` 跳转、前后端反向代理 |
| `deploy.env.example` | 生产环境变量名称和安全占位示例 |
| `backend/Dockerfile` | 构建 FastAPI 生产镜像，包含 Alembic 和账号维护脚本 |
| `frontend/src/app/manifest.ts` | PWA Manifest |
| `frontend/public/icons/*` | 普通、maskable 和 monochrome 应用图标 |
| `frontend/public/screenshots/login-mobile.png` | 不含真实账号和家庭数据的移动端安装预览图 |
| `frontend/public/.well-known/assetlinks.json` | Android 包与生产域名的公开关联声明 |

真实生产变量只保存在 VPS `/opt/eiheizone/.env`，不写入 Git、镜像、发布记录或聊天消息。

## 6. PWA 发布

线上公开资源：

```text
https://eihei.zone/manifest.webmanifest
https://eihei.zone/icons/icon-192.png
https://eihei.zone/icons/icon-512.png
https://eihei.zone/icons/icon-maskable-512.png
https://eihei.zone/icons/icon-monochrome-512.png
https://eihei.zone/screenshots/login-mobile.png
```

Manifest 关键配置：

| 字段 | 值 |
| --- | --- |
| `name` / `short_name` | `EiheiZone` |
| `id` / `start_url` | `/family` |
| `scope` | `/` |
| `display` | `standalone` |
| `orientation` | `portrait-primary` |
| `lang` | `zh-CN` |
| `categories` | `lifestyle` |

页面 viewport 为 `width=device-width, initial-scale=1`，没有设置 `user-scalable=no` 或 `maximum-scale=1`；浏览器和 PWA 未主动禁止双指缩放，当前 Android APK 的 WebView 壳关闭双指缩放。

V1 不注册 Service Worker，不提供离线使用，也不离线缓存家庭真实数据。PWABuilder 因此仍显示 1 个 Service Worker 建议，但必需项为 0，且不影响 PWA 或 Android APK 的在线使用。

## 7. Android APK 打包与分发

### 7.1 打包方式

标准发布路径是使用 [PWABuilder](https://www.pwabuilder.com/) 在线检查 PWA 并生成 Android TWA，再以父母实际使用的安卓手机作为放行门槛。本次在线 TWA 无法在目标设备稳定启动，因此临时使用本机 Android SDK 将 PWABuilder 导出的工程调整为 WebView APK，并使用原签名密钥完成构建与签名。

最终 APK 通过 WebView 直连 `https://eihei.zone/family`。APK 只提供安卓入口，Next.js、FastAPI 和 PostgreSQL 仍运行在云服务器上。

生成产物：

| 文件 | 用途 | 是否分发给父母 |
| --- | --- | --- |
| `EiheiZone.apk` | 安卓侧载安装包 | 是 |
| `EiheiZone.aab` | Google Play 等应用商店提交包 | 否，当前留存 |
| `assetlinks.json` | 域名、包名与签名指纹关联 | 否，已部署到网站 |
| `signing.keystore` | 后续新版 APK/AAB 签名 | 否，必须保密 |
| `signing-key-info.txt` | 签名别名和密码 | 否，必须保密 |
| `Readme.html` | PWABuilder 说明 | 否 |

### 7.2 产物校验值

| 产物 | SHA-256 |
| --- | --- |
| `EiheiZone-1.0.2-webview-android.zip` | `0592E7590A9AE77F79DAB165D23F7BDC5F86DEB55866FE5A3E275501C0F90044` |
| `EiheiZone.apk` | `9B5D8DEC044B2455FD10C189DBD95068D2DDB87A698C5FEC90F944F56263CF4B` |
| `EiheiZone.aab` | `7B6A6D9B5EE98D3C7EDE8EE3FB4EC48314EDBD829954CE01D49FD19A01D0C1EF` |

APK 验证结果：

- 包名：`zone.eihei.app`；
- `versionCode=3`；
- `versionName=1.0.2.0`；
- 最低 Android API 21，即 Android 5；
- 目标 API 35；
- APK Signature Scheme v1、v2、v3 验证通过；
- 单一签名者；
- APK 证书 SHA-256 与线上 `assetlinks.json` 完全一致。

### 7.3 Digital Asset Links

生产地址：

```text
https://eihei.zone/.well-known/assetlinks.json
```

实际验证结果：

- HTTP 状态为 `200`；
- Content-Type 为 `application/json`；
- 包名为 `zone.eihei.app`；
- Google Digital Asset Links 官方接口能够识别域名、包名和证书指纹的关联。

当前 WebView APK 不依赖 Digital Asset Links 才能无地址栏启动；线上关联文件继续保留，供域名与签名校验及后续兼容使用。

### 7.4 分发原则

父母只接收 `EiheiZone.apk`，不能接收完整 Android ZIP、AAB、keystore 或 signing-key-info。可以通过数据线、QQ 文件或私人网盘传输 APK；聊天软件阻止 `.apk` 时，可以另建一个**只包含 APK**的 ZIP。

安装时如果系统要求“允许安装未知应用”，只临时授权当前文件管理器或传输工具，安装完成后关闭该权限。

## 8. 验证记录

### 8.1 应用测试与构建

| 检查项 | 结果 |
| --- | --- |
| 第五阶段需求追踪 | FR-001～FR-045，`45/45` 通过 |
| 第五阶段后端测试 | `229 passed` |
| 本次前端完整测试 | `82 passed` |
| PWA Manifest 测试 | `3 passed` |
| TypeScript | 通过 |
| ESLint | `0 errors`；coverage 生成文件有 2 个既有 warning |
| Next.js 生产构建 | 通过，生成 `/manifest.webmanifest` |
| 前端 VPS Docker 镜像构建 | 通过 |
| Git 暂存区敏感信息检查 | 未发现真实密码、SSH 私钥或签名秘密 |

### 8.2 线上验证

| 检查项 | 结果 |
| --- | --- |
| HTTPS 主站 | `200` |
| HTTP 跳转 | `308` 到 HTTPS |
| `www` 跳转 | `301` 到主域名 |
| `/api/v1/health` | `200`，返回健康状态 |
| PostgreSQL | healthy |
| FastAPI | healthy，启动时执行 `alembic upgrade head` |
| Next.js | running，前后端同源通信正常 |
| Caddy | running，监听 `80/443` |
| Owner 登录与管理页面 | 通过 |
| Family 登录与家庭页面 | 通过 |
| Family 越权访问 Owner | 返回 `403` |
| Public、退出和再次登录 | 通过 |
| Compose 整套容器重启 | 服务恢复，账号与数据仍保留 |
| PWABuilder 在线复检 | `canPackage=true`，必需项 0 |
| Manifest、图标、截图 | HTTPS 正常返回 |
| Digital Asset Links | 线上和 Google 官方接口验证通过 |

电脑和手机可以使用同一个账号同时登录。每次登录建立独立服务器 Session；一个设备退出只删除当前 Session，不会挤掉其他设备。Session 固定有效期为 30 天，密码重置或账号停用会使该账号的全部 Session 失效。

## 9. 日常运维

登录 VPS 后进入：

```bash
cd /opt/eiheizone
```

常用只读检查：

```bash
sudo docker compose ps
sudo docker compose logs --tail=100 frontend
sudo docker compose logs --tail=100 backend
sudo docker compose logs --tail=100 caddy
sudo docker compose logs --tail=100 db
```

重启整套服务：

```bash
sudo docker compose restart
```

手工发布基本顺序：

1. 本地完成相关测试、类型检查、Lint 和生产构建；
2. 确认生产 `.env`、数据库 Volume 和当前容器状态；
3. 涉及数据库 Migration 时先完成可恢复的备份；
4. 上传变更并构建对应镜像；
5. 使用 Compose 更新服务；
6. 验证健康接口、HTTPS、登录和受影响业务流程；
7. 记录版本、提交、Migration 和异常情况。

Web 页面和业务更新通常不需要重新分发 APK。只有 Android 包配置、应用身份、图标或商店版本发生变化时，才需要重新构建 APK/AAB。

## 10. 安全与备份边界

### 10.1 不得公开或提交的文件

- VPS `.env`；
- SSH 私钥；
- `signing.keystore`；
- `signing-key-info.txt`；
- 包含上述签名文件的完整 Android ZIP；
- 数据库备份和真实家庭数据。

“生产秘密”是指真实 `.env` 中的数据库密码和 CSRF 密钥、SSH 私钥、APK 签名密钥、签名密码、数据库备份和真实家庭数据。

GitHub 交付范围只包含应用代码和正式交付文档，不包含第六阶段本地资料目录中的 PEM、完整 Android ZIP、keystore、signing-key-info 或其他私密文件。正式文档只记录文件用途、管理原则和公开校验值，不记录任何秘密值。应用 Git 仓库和正式交付文档的秘密扫描均未发现真实凭证，因此该项验收通过。

### 10.2 APK 升级约束

后续覆盖安装新版必须同时满足：

- 包名继续使用 `zone.eihei.app`；
- 使用同一个 `signing.keystore`；
- 使用匹配的别名和密码；
- `versionCode` 大于当前值 `1`；
- 如果签名证书变化，同步更新线上 `assetlinks.json`。

签名密钥丢失后，无法继续以原应用身份覆盖升级，只能更换包名并让用户安装另一个应用。

### 10.3 数据备份现状

当前生产数据由 PostgreSQL named volume 持久化，可以经受容器重建和 VPS 正常关机、开机，但不能覆盖 VPS 磁盘损坏、整机销毁或误删数据。

V1 暂不建设异机加密备份和独立恢复演练。项目创建者理解并接受“VPS 整机数据损坏时可能无法恢复历史数据”的剩余风险，该事项进入后续运维 Backlog，不作为第六阶段交付阻断项。早期方案中的“每日备份、RPO 24 小时、RTO 2 小时”不再表述为 V1 已实现能力。

## 11. 验收结果与接受的遗留事项

| 编号          | 事项             | 最终状态        | V1 处置结论                                                                                                                      |
| ----------- | -------------- | ----------- | ---------------------------------------------------------------------------------------------------------------------------- |
| RELEASE-001 | 前端生产依赖安全告警     | Accept Risk | `npm audit --omit=dev` 仍报告 PostCSS/Sharp 共 3 个 high severity 告警；家庭小范围 V1 接受风险，后续明确升级 Next.js 并回归，不执行 `npm audit fix --force` |
| RELEASE-002 | 完整 Migration 链 | Deferred    | 生产 `alembic upgrade head` 和模块 Migration 测试已通过；完整降级与再升级只允许在临时数据库补做，不在生产库实验                                                    |
| RELEASE-003 | 父母安卓真机 APK     | Pass        | APK 安装、启动、登录和核心使用验收通过                                                                                                        |
| RELEASE-004 | PWA 备用入口       | Pass        | 父母安卓真机添加到桌面和启动验收通过                                                                                                           |
| RELEASE-005 | 异机备份与恢复        | Deferred    | V1 暂缓，接受 named volume 无法覆盖整机损坏的风险，转入后续运维                                                                                     |
| RELEASE-006 | 生产秘密交付边界       | Pass        | GitHub 交付代码和正式文档不包含真实 `.env`、PEM、keystore、签名密码或真实家庭数据                                                                        |
| RELEASE-007 | VPS 整机恢复验证     | Pass        | VPS 关机、开机后 Docker 与四个 Compose 服务自动恢复，站点访问正常                                                                                  |

压力测试、Cloudflare、CI/CD、文件上传、通知、应用商店上架、完整离线能力和异机备份不属于 V1 交付范围，按实际需求进入后续维护或 V1.1 Backlog。

## 12. V1 最终签署清单

- [x] V1 功能和权限正式测试通过；
- [x] 生产 Docker Compose、Caddy 和环境变量模板完成；
- [x] 域名、DNS、HTTPS 和同源 API 完成；
- [x] Owner、Family 和 Public 核心线上流程通过；
- [x] PWA Manifest、图标、截图和缩放边界完成；
- [x] Android WebView APK/AAB、签名和 Digital Asset Links 完成；
- [x] V1 Git 发布基线提交完成；
- [x] 生产依赖 high severity 告警已记录并作出 V1 风险接受决定；
- [x] 完整 Migration 链明确转入临时环境后续验证，不在生产库执行；
- [x] 父母安卓真机 APK 与 PWA 验收通过；
- [x] 异机备份与恢复明确暂缓并接受剩余风险；
- [x] GitHub 交付范围不包含生产秘密；
- [x] VPS 整机关机、开机后的自动恢复验证通过；
- [x] 2026-08-05 最终签署结论：Accept。

## 13. 最终状态

**最终结论：Accept。EiheiZone V1 已完成核心开发、正式测试、公网部署、PWA 发布、Android WebView APK 构建、父母安卓真机验收和 VPS 整机恢复验证，已经达到家庭小范围使用与交付标准。生产依赖告警、完整 Migration 链和异机备份作为已知且接受的遗留事项转入后续维护，不阻止第六阶段完成。V1 至此结束，后续工作进入运行维护或 V1.1。**
