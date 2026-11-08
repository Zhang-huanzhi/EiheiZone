---
id: T004
title: 家庭成员展示空间（members）模块
type: feat
status: Accepted
created: "2026-11-08"
updated: "2026-11-08"
branch: feat/004-member-spaces
---

# T004 家庭成员展示空间（members）模块

## 1. 背景与目标

### 1.1 需求背景与痛点分析

随着家庭门户系统（EiheiZone）的长期运行，现有的三个一级模块各有侧重：`posts` 承载按时间流逝的家庭近况，`qas` 承载具体问题与解答，`expenditures` 承载重大支出记录。但在“认识彼此与沉淀个人轨迹”维度仍存在三项核心痛点：

- **动态流（Post）留不住“人”的完整画像**：近况动态按时间倒序流逝，半年后便沉底，无法形成对某一位家庭成员的系统性认识。
- **家庭内部存在“熟悉的陌生人”现象**：家人清楚彼此的日常起居，但年轻一代的精神世界、长线爱好与折腾成果长辈并不了解；父母年轻时经历过的大风大浪、当年的梦想与最骄傲的往事，晚辈也缺乏深入了解的窗口。
- **微信朋友圈的局限性**：朋友圈三天可见、压箱底的老照片散落在各自手机中面临丢失风险，家庭内部缺乏一个**只属于全家人、可沉淀数十年的“数字档案卡与个人画廊”**。

### 1.2 目标用户角色分析（User Personas）

| 角色 | 典型特征与心理 | 核心痛点与诉求 | 在该模块的期望行为 |
| --- | --- | --- | --- |
| 年轻一代（Owner / 年轻成员） | 习惯数字化表达、重视审美与个性、有展示欲 | 不想写死板八股文，想放有质感的封面照片、摄影作品与个性签名 | 挑一张好看的横幅封面，点选专属强调色，写一两句随性签名，上传日常摄影 |
| 长辈一代（父母等 Family 成员） | 不会复杂排版、提笔忘字、害怕复杂软件，但内心有珍藏老照片的冲动 | 复杂工具不会用；填写死板表单有心理负担 | 管理员可代为设置老照片头像；长辈只需直接批量上传老照片，即可生成精美画廊 |

### 1.3 业务目标与成功检验信号

本模块不以日常沟通效率或日活（DAU）衡量，核心目标是**以图片为主、极简签名简介为辅，为每位家庭成员建立长期的家庭数字资产**。检验成功的质性信号为：

1. **零负担极简表达**：拒绝死板八股文或尴尬说教文案；无需繁琐建相册或填表，选图后即可一键批量入库；
2. **引发线下与电话讨论**：家人看到主页新发的照片后，在线下聚会或通话中主动聊起往事；
3. **长期时间沉淀**：半年至一年后，每位成员主页自然生长出多张珍贵照片与阶段签名，形成生活印记。

## 2. 范围与交互设计演进

### 2.1 本次范围

- **个人形象与极简名片（Profile & Signature）**：
  - 个人头像（Avatar）、顶部横幅封面（Banner）；
  - 成员空间昵称（`family_title`，未填时回退显示账号 `display_name`；与 `users` 表完全解耦独立，不改变右上角全局账号显示）；
  - 单一自由简介与个性签名（`about_me`，多行文本，自由填写或纯净留白，彻底移除死板的“爱好/绝活/坐标/人生小记”等割裂填空框）；
  - 内置 5 种预设强调色（深海蓝、暖阳橙、森林绿、复古酒红、水墨雅灰），全面联动头像描边、昵称色标、上传按钮与照片数徽标。
- **全景覆盖与环境虚化卡片设计（Cover Overlay with Ambient Blur）**：
  - 列表页与主页顶部采用统一的大图全景覆盖架构（高度 288px ~ 352px），彻底解决图片截断局促问题；
  - 底层搭载 `scale-125 blur-2xl opacity-50` 环境色虚化光晕，配合电影级暗调渐变遮罩（`from-black/90 via-black/50 to-black/20`），确保画面主体完整舒展，文字与头像立体清晰。
- **个人图库瀑布流（Flat Photo Masonry）**：
  - 扁平化极简图库，无需繁琐创建中间相册，个人主页直接呈现响应式瀑布流；
  - 手机端采用精致双列瀑布流（`columns-2 gap-2.5`），平板与桌面端自适应扩至 3~4 列，彻底告别移动端单列笨重长图刷屏体验；
  - 支持单次批量选择 1–9 张照片直接极速上传，彻底移除时间、地点、说明等冗余输入框；
  - 全屏沉浸式照片查看器（Lightbox），支持键盘方向键与触屏滑动翻页，采用**行内平滑二次确认交互**（“删除照片” $\rightarrow$ “确认删除” / “取消”）代替生硬的系统原生 `window.confirm` 阻塞弹窗。
- **界面纯净化与环境适配（Clean UI & Environment）**：
  - 移除多余的置顶“我的空间”大卡片与指导文案，列表页直接平铺所有家庭成员卡片，自己点击自己的主页即可进入；
  - 根布局适配浏览器翻译扩展（`suppressHydrationWarning`），彻底消除客户端属性水合不一致警告。
- **权限与安全闭环**：
  - 仅对已登录的 `Family` 与 `Owner` 开放阅读（全家互通），未登录 `Public` 严禁访问；
  - 每位成员可编辑自己的空间；`Owner` 除维护本人空间外，还可代任意家庭成员维护主页资料（助力长辈建档破冰）。

### 2.2 不做事项

- **不做复杂的自由排版与拖拽建站编辑器**：保持极简统一的画廊风格，杜绝版面失控；
- **不做即时评论或点赞系统**：家庭内部无需点赞攀比，通过日常沟通自然交流；
- **不做单图或单相册的家庭内隔离权限**：进入家庭空间即全家人坦诚相待，默认全家可见；
- **不开放公开（Public）访问入口**：家庭老照片属于私域核心资产，不暴露给匿名访客。

## 3. 验收标准

- [x] 未登录访客访问 `/api/v1/members*` 返回 `401 UNAUTHORIZED`，访问 `/api/v1/media/member-images/{id}` 返回 `404 IMAGE_NOT_FOUND`；
- [x] 已登录 `Family` 与 `Owner` 可查看所有活跃家庭成员的卡片列表、个人空间主页、图库照片与成员图片（响应头包含 `Cache-Control: private, no-store` 与 `X-Content-Type-Options: nosniff`）；
- [x] `Family` 成员只能修改自己的主页与照片，修改其他成员空间返回 `403 FORBIDDEN`；`Owner` 可以修改任意成员的资料与照片；
- [x] 所有写接口（`PUT/POST/PATCH/DELETE`）强制校验绑定当前会话的 CSRF Token；
- [x] 上传成员图片自动执行 EXIF 方向矫正（`ImageOps.exif_transpose`）、剥离原始元数据并重编码为 WebP（最大边 2048px，单张 $\le 5\text{ MB}$）；
- [x] `cleanup_orphan_images` 将 `member_images.storage_key` 纳入 `known_keys`，确保 `media-cleanup-worker` 扫描孤立文件时绝不误删已绑定的成员头像、封面与照片，同时正常清理超过 24 小时的过期 `pending` 记录；
- [x] 前端 `/family/members` 与 `/owner/members` 完整支持极简全景卡片、5 套强调色联动、单一签名编辑、批量选图直传、移动端双列瀑布流与行内确认 Lightbox 删除；
- [x] Alembic Migration `a7c8d9e0f1b2` 支持从 `f1a2b3c4d5e6` 降级与升级，本地开发库已成功升级；前后端静态检查、单元测试与构建全部通过。

## 4. 方案与技术影响

### 4.1 关键技术方案取舍

| 方案 | 取舍 |
| --- | --- |
| 独立创建与 `users` 解耦的 `members` 账号体系 | 不选：导致登录账号与展示空间脱节，“本人可编辑”缺乏唯一身份锚点 |
| 与 `users` 表 `1:1` 绑定（`member_profiles.user_id`），目录以所有 `ACTIVE` 用户为基准左连接查询 | 采用：管理员创建账号后成员自动出现在名录中，首次保存自动 Upsert，天然支持本人自维护与 Owner 代维护 |
| 复用 `post_images` 表存储成员头像、封面与照片 | 不选：`post_images` 带有九宫格 `position BETWEEN 0 AND 8` 与 `post_id` 约束，混入成员长期资产会污染领域边界 |
| 新建独立 `member_images` 表，并接入 `cleanup_orphan_images` 的 `known_keys` 与过期清理 | 采用：存储在 `media/members/YYYY/MM/{uuid}.webp`，按引用计数安全清理拆离图片，并防止 `media-cleanup-worker` 在全目录扫描时误删成员照片 |
| 维持繁琐的主题相册层级 | 不选：用户需要先建相册再点进相册看图，链路过长，操作疲劳 |
| 扁平化图库瀑布流（Flat Photo Masonry） | 采用：在底层相册模型保持兼容的前提下，API 直接聚合平铺照片，前端在个人主页直接呈现双列/多列瀑布流并支持一键批量传图 |
| 系统原生 `window.confirm` 对话框 | 不选：弹窗样式突兀，破坏全屏深色 Lightbox 的沉浸视觉，且存在平台不一致问题 |
| Lightbox 行内双态二次确认（Inline Confirmation） | 采用：在操作栏原位平滑展开“确认删除 / 取消”按钮，翻页或退出时自动复位，体验自然且防误触 |

### 4.2 数据库与接口设计（Design）

- **新增数据表（Migration `a7c8d9e0f1b2`）**：
  - `member_images`：保存成员空间 WebP 图片元数据、上传人 `owner_id`、归属成员 `target_user_id`、状态（`pending` / `attached` / `cleanup_pending`）及清理重试统计；
  - `member_profiles`：与 `users.id` 一对一主键关联，保存 `family_title`（空间昵称，独立于 `users.display_name`）、`status_text`、`about_me`（自由签名简介，$\le 500$ 字）、`avatar_image_id`、`banner_image_id`、`accent_color`；
  - `member_albums`：保存成员相册底层记录（默认主相册支持扁平图库）；
  - `member_photos`：保存单张照片及其属性（`image_id`、`taken_at_label`、`location`、`story`、`position`）。
- **REST API 端点**：
  - `GET /api/v1/members`：获取全部活跃家庭成员卡片列表（包含昵称、签名、封面、头像、照片统计）；
  - `GET /api/v1/members/{user_id}`：获取成员空间详情（包含个人主页信息及平铺聚合照片列表 `photos`）；
  - `PUT /api/v1/members/{user_id}/profile`：Upsert 成员空间昵称、个性签名与外观主题色；
  - `POST /api/v1/members/{user_id}/uploads/image`：上传成员空间图片；
  - `POST /api/v1/members/{user_id}/photos`：直接批量添加照片至成员图库；
  - `DELETE /api/v1/members/{user_id}/photos/{photo_id}`：直接按照片 ID 删除图库照片；
  - `GET /api/v1/media/member-images/{image_id}`：鉴权读取成员图片文件。

### 4.3 实现拆解（Implementation）

1. **后端领域层（`backend/app/modules/members/`）**：按 `router -> service -> repository` + `image_service` 分层实现，统一在 Service 层执行权限校验与引用安全删除，支持直传直删接口。
2. **媒体清理协同（`backend/app/modules/posts/image_service.py`）**：将 `MemberImage` 合并入 `cleanup_orphan_images` 的过期候选列表与 `known_keys` 集合。
3. **前端功能与路由层（`frontend/src/features/members/` 与 `src/app/{family,owner}/members/`）**：
   - 主导航栏 `AreaNavigation` 增加「家庭成员」一级入口；
   - 实现 `MemberDirectory`（全景覆盖大卡片 + 环境光虚化）、`MemberSpaceView`（主页全景大图 + 移动端双列瀑布流）、`MemberProfileEditor`（空间昵称与单一签名编辑）、`MemberStoryLightbox`（行内二次确认删除）；
   - 修复 Next.js 根布局在第三方浏览器翻译插件环境下的 Hydration mismatch。
4. **版本控制配置**：
   - 更新 `.gitignore` 将运行期上传的 `backend/media/members/` 排除在版本控制之外。

### 4.4 上线与回滚方案（Release & Rollout）

1. **上线步骤**：
   - PR 通过 CI 检查后合并至 `main`；
   - GitHub Actions 触发部署脚本，构建容器镜像，启动时自动执行 `alembic upgrade head` 升级至 `a7c8d9e0f1b2`，并校验健康检查接口。
2. **兼容性与回滚边界**：
   - `a7c8d9e0f1b2` 为纯增量建表 Migration，不改动任何既有业务表结构；
   - 如需回退，在维护窗口执行 `alembic downgrade f1a2b3c4d5e6`。

## 5. 实施与检查记录

| 检查 | 结果 | 证据 |
| --- | --- | --- |
| 分支创建 | `PASS` | 从 `main` 切出 `feat/004-member-spaces` |
| 后端 Ruff 静态检查 | `PASS` | `.\backend\.venv\Scripts\ruff.exe check backend`（`All checks passed!`） |
| 后端测试库 Migration 升降级与契约/集成测试 | `PASS` | `pytest -c backend\pyproject.toml backend\tests\members backend\tests\integration`（`49 passed` 全部通过） |
| 本地开发数据库 Migration 升级 | `PASS` | `alembic upgrade head` 成功升级本地开发库（`Running upgrade f1a2b3c4d5e6 -> a7c8d9e0f1b2`） |
| 前端 ESLint 与 TypeScript 类型检查 | `PASS` | `npm run lint`、`npm run typecheck` 零告警零报错通过 |
| 前端 Vitest 单元测试与 Next.js 生产构建 | `PASS` | `npm test -- --run`（`37 passed (37), 118 passed (118)`）、`npm --prefix frontend run build` 全部成功通过 |

## 6. 遗留风险与后续事项

- 成员空间照片随时间长期积累后，`media_data` 卷体积会逐步增长；后续若启用 `T002`（COS 每日加密备份），备份脚本中的 `/app/media` 归档已天然覆盖 `media/members/` 目录，无需额外修改备份路径。
