# Personal Family Portal V1 架构设计

## 1. 文档信息

| 项目   | 内容                                  |
| ---- | ----------------------------------- |
| 项目名称 | EiheiZone（Personal Family Portal）     |
| 文档名称 | V1 架构设计                             |
| 项目阶段 | V1 OOA / 基本设计 / OOD                 |
| 文档版本 | v0.9                                |
| 文档状态 | Accept                              |
| 创建日期 | 2026-07-13                          |
| 更新日期 | 2026-08-04                          |
| 维护者  | Eihei                               |
| 目标读者 | 项目开发者、未来维护者、作品集查看者                  |
| 需求基线 | `01_v1_requirements.md` v0.4 Accept |
| 适用范围 | 本文档定义 V1 阶段的权限、对象、数据、页面、API 与系统大框架  |

### 1.1 文档目的

本文档用于把已经确认的 V1 需求转换为系统的大框架设计，作为后续任务分解和开发实现的依据。

需求文档负责说明“V1 做什么”，本文档负责说明“V1 准备怎样实现”。本阶段主要确定权限、核心对象、数据结构、页面和 API 的整体安排，不展开具体代码、完整测试用例和发布操作。

### 1.2 设计范围

本文档覆盖 V1 的以下内容：

- Public、Family、Owner 三类角色的权限与登录方式；
- User、Post、QA、Expenditure 等核心对象及其关系；
- Next.js、FastAPI 和 PostgreSQL 的职责与连接方式；
- Public Home、Dashboard、Owner Workspace 等页面大框架；
- Auth、Post、QA、Expenditure、Dashboard 的 API 大框架；
- 支撑上述内容所需的项目目录和关键业务流程。

本文档不为 V1 以外的功能提前设计。图片上传、评论、通知、复杂搜索、AI、pgvector、多语言、用户管理后台等内容仍属于后续版本范围。

### 1.3 设计依据

| 资料 | 用途 |
|---|---|
| `01_v1_requirements.md` | V1 功能、权限、数据需求和验收标准 |
| `需求分析_问题与决策备忘/x1.md` | 第一阶段已经确认的需求问题 |
| `技术栈x1.md` | 项目的技术选型 |
| `开发流程/确定x1.md` | 架构设计阶段的范围和产出 |
| `图 风格&主题/确定.md` | PlantUML 图表风格 |

如果设计内容与正式需求冲突，以已经接受的 `01_v1_requirements.md` 为准。无法从现有资料确定、且会影响架构的事项，需要先向项目创建者确认。

### 1.4 V1 固定参数

下列参数是 V1 设计基线。实现阶段应同时落实到集中配置、Pydantic 校验、数据库约束或 API 行为，不能由不同模块分别使用不一致的值。

| 参数 | V1 结论 |
|---|---|
| Session | 30 天固定有效期，不滑动续期 |
| Session Cookie | `pfp_session` |
| CSRF Cookie | `pfp_csrf` |
| 列表分页 | `limit` 默认 20、最大 100 |
| Dashboard | 每类最近 5 条记录 |
| Post | 标题 120 字符、正文 10,000 字符 |
| QA | 问题 2,000 字符、回答 10,000 字符 |
| Expenditure | 分类 80 字符、说明 2,000 字符 |
| 金额 | PostgreSQL `NUMERIC(18,4)`，API 最多四位小数 |
| 初始显示时区 | `Asia/Shanghai`，可通过环境变量调整 |
| 日志级别 | 生产默认 `INFO` |
| 请求标识 | 每个请求生成 UUID，并通过统一错误结构返回 |

## 2. 总体架构

### 2.1 架构方案

V1 采用前后端分离、分层的模块化单体架构。

前端和后端分别使用 Next.js 与 FastAPI 开发，但后端暂不拆分为多个服务。Auth/User、Post、QA、Expenditure 和 Dashboard 按业务模块组织在同一个 FastAPI 应用中，共用一个 PostgreSQL 数据库。

该方案适合 V1 的小规模家庭使用场景：结构清楚，部署和调试成本较低，同时保留明确的业务模块边界，后续可以在不推翻整体结构的情况下继续扩展。

V1 不引入微服务、Redis、消息队列、应用文件存储和 pgvector。它们只有在后续出现明确需求时再加入。

### 2.2 系统组成

| 组成     | 技术                                 | 主要职责                                  |
| ------ | ---------------------------------- | ------------------------------------- |
| Web 前端 | Next.js 16、React 19、TypeScript     | 页面展示、路由、表单交互和调用后端 API                 |
| API 后端 | FastAPI、Pydantic v2、SQLAlchemy 2.x | 登录认证、权限判断、业务规则、数据校验和数据库访问             |
| 数据库    | PostgreSQL 17                      | 保存用户、Post、QA 和 Expenditure 数据         |
| 数据库迁移  | Alembic                            | 管理数据库结构的版本变化                          |
| 登录入口保护 | Caddy + FastAPI                    | HTTPS、Origin/CSRF 和后端认证校验                       |
| 统一入口   | 同一站点域名                             | 页面请求进入 Next.js，`/api/*` 请求转发给 FastAPI |

用户只访问一个站点域名。生产请求先经过 Caddy；浏览器访问普通路径时获得 Next.js 页面，访问 `/api/*` 时转发到 FastAPI。这样可以简化 Cookie、跨域和前后端地址配置。

### 2.3 前后端职责

Next.js 负责用户界面，不直接连接 PostgreSQL，也不保存后端专属业务规则。前端可以根据当前用户隐藏或显示页面和按钮，但这种处理只用于改善使用体验，不能作为真正的权限保护。

FastAPI 是系统的业务与数据入口，负责验证登录身份、检查角色和内容可见范围。所有数据库读写都必须经过 FastAPI；即使前端出现错误或有人绕过页面直接请求 API，后端仍应拒绝越权操作。

PostgreSQL 只接受 FastAPI 的访问。Public、Family、Owner 以及 Next.js 都不能直接访问数据库。

### 2.4 模块划分

| 模块 | 主要职责 |
|---|---|
| Auth/User | 登录、退出、当前用户识别和角色判断 |
| Post | 近况的创建、编辑、删除、列表、详情和可见范围控制 |
| QA | Family/Owner 提问、Owner 回答、状态变化和问答查看 |
| Expenditure | 重大支出的创建、编辑、删除和查看 |
| Dashboard | 按当前用户权限聚合最近的 Post、QA 和 Expenditure |

Dashboard 只聚合其他模块已有的数据，不建立独立的 Dashboard 业务数据。各模块可以共用认证和数据库基础设施，但一个模块不应绕过另一个模块已经确定的权限规则。

每个业务模块内部按照 `Router -> Service -> Repository` 分层。Router 负责 HTTP 输入输出，Service 负责业务规则和事务，Repository 负责数据访问。模块之间通过对方的 Service 或公开接口协作，不直接调用对方的 Repository。

### 2.5 总体架构图

下图只表达 V1 的主要运行组件和请求方向，不展开云厂商控制台与代码内部细节。
![[Pasted image 20260713175954.png]]


### 2.6 关键架构决定

| 决定    | V1 选择                             | 理由                             |
| ----- | --------------------------------- | ------------------------------ |
| 后端形态  | 分层的模块化单体                         | 按业务划分模块，模块内部按控制层、业务层和数据层组织       |
| 前后端关系 | Next.js 调用 FastAPI，Next.js 不直连数据库 | 统一业务和权限入口，避免规则分散               |
| 访问入口  | 同一域名，`/api/*` 转发到 FastAPI         | 简化 Cookie、CORS 和环境配置           |
| 登录凭证  | HttpOnly Cookie                   | 浏览器自动携带，前端 JavaScript 无法直接读取凭证 |
| 权限控制  | 前端提示，后端强制执行                       | 防止绕过页面直接读取或修改受保护数据             |
| 数据存储  | 单个 PostgreSQL 数据库                 | 满足 V1 关系数据和事务需求，结构简单           |
| 扩展策略  | 按实际需求增加组件                         | 不为图片、通知、AI 等后续功能提前增加复杂度        |

## 3. 权限与认证

### 3.1 用户角色

系统有 Public、Family 和 Owner 三类访问身份。Public 是未登录状态，不在数据库中保存用户记录；Family 和 Owner 通过各自的 User 账号登录。

| 角色 | 定位 | 主要能力 |
|---|---|---|
| Public | 未登录访客 | 访问公开首页和公开 Post |
| Family | 家人用户 | 查看家人内容、提交问题 |
| Owner | 项目创建者 | 查看全部内容、提交问题，管理 Post、QA 和 Expenditure |

每位 Family 使用独立账号，不共享登录凭证。V1 不提供用户管理和自助改密页面，Owner 通过服务器脚本创建账号或重置密码，并私下交付随机初始密码。数据库只保存经过 Argon2id 处理的密码哈希，不保存明文密码。

### 3.2 登录与会话

V1 使用数据库服务端 Session。用户登录成功后，FastAPI 创建 Session，并通过 HttpOnly Cookie 向浏览器返回随机会话凭证；后续请求由浏览器自动携带该 Cookie，FastAPI 查询 `sessions` 表并识别当前 User。

会话方案遵循以下规则：

- Session 保存在 PostgreSQL，不依赖应用内存或 Redis；
- Session Cookie 使用 `Secure`、`HttpOnly`、`SameSite=Lax` 和 `Path=/`；
- Cookie 中只保存随机凭证，不保存角色、密码或其他业务数据；
- Session 固定有效期为 30 天，V1 不做滑动续期，过期后必须重新登录；
- 退出登录时删除服务器端 Session，并清除浏览器 Cookie；
- 账号被停用或密码被人工重置时，相关 Session 应全部失效；
- 创建、修改和删除请求必须通过签名 Double Submit Cookie 方式的 CSRF Token 校验；
- FastAPI 同时比较 CSRF Cookie 与 `X-CSRF-Token` 请求头、验证签名，并校验请求 `Origin`；
- 登录成功后轮换 CSRF Token，并将新 Token 与当前 Session 关联。

登录请求由 FastAPI 完成 CSRF、Origin、密码和 Session 校验，应用统一返回模糊的登录失败信息。后续如果出现明确的暴力破解风险，再增加应用层限流或边缘防护。

登录身份只表示“当前用户是谁”，不等于用户可以访问全部数据。每次业务请求仍需继续执行角色和数据范围检查。

### 3.3 权限矩阵

| 功能 | Public | Family | Owner |
|---|:---:|:---:|:---:|
| 访问公开首页 | 可以 | 可以 | 可以 |
| 查看公开 Post | 可以 | 可以 | 可以 |
| 查看仅家人可见 Post | 不可以 | 可以 | 可以 |
| 创建、编辑、删除 Post | 不可以 | 不可以 | 可以 |
| 查看 QA | 不可以 | 可以 | 可以 |
| 提交 QA 问题 | 不可以 | 可以 | 可以 |
| 回答 QA | 不可以 | 不可以 | 可以 |
| 查看 Expenditure | 不可以 | 可以 | 可以 |
| 创建、编辑、删除 Expenditure | 不可以 | 不可以 | 可以 |
| 访问 Dashboard | 不可以 | 可以 | 可以 |
| 访问 Owner Workspace | 不可以 | 不可以 | 可以 |
| 管理用户 | 不可以 | 不可以 | 不可以 |

Owner 是 V1 唯一具有内容管理能力的角色。Family 可以查看所有 Family 可见的 QA，不限定为只看自己提出的问题。Expenditure 始终只对 Family 和 Owner 可见，不提供单条公开设置。

### 3.4 权限执行方式

权限在前端、Router、Service 和 Repository 四个位置共同落实，但各位置的职责不同：

| 位置 | 职责 |
|---|---|
| Next.js | 根据当前身份提供正确页面和操作入口，仅用于界面体验 |
| Router | 验证 Session，并拒绝明显不符合角色要求的请求 |
| Service | 执行最终业务权限，例如只有 Owner 可以回答 QA |
| Repository | 在查询中加入数据范围条件，例如 Public 只能查询公开 Post |

前端隐藏按钮不能代替后端权限检查。模块之间也不能通过直接调用其他模块的 Repository 绕过其 Service 权限规则。

未登录用户请求必须登录的 API 时返回未认证结果；已登录但角色不符时返回无权限结果。查询列表时直接过滤不可见数据，查询单条不可见内容时不返回内容详情，避免泄露受保护数据是否存在。

## 4. 领域对象与数据设计

### 4.1 核心对象

| 对象 | 含义 | 主要关系 |
|---|---|---|
| User | 可登录的 Family 或 Owner 账号 | 拥有 Session；可以创建或处理业务内容 |
| Session | 一次服务器端登录会话 | 必须属于一个 User |
| Post | Owner 发布的生活近况 | 由 Owner 创建，通过可见范围控制读取权限 |
| QA | 一次 Family/Owner 提问和一次 Owner 回答 | 由 Family 或 Owner 提问，可以由 Owner 回答 |
| Expenditure | 一条重大支出记录 | 由 Owner 创建，Family 和 Owner 可查看 |

Dashboard 不是独立领域对象，也不建立数据表。它通过应用服务聚合 Post、QA 和 Expenditure 的最近数据。

V1 将问题和回答放在同一个 QA 对象中。新 QA 的回答内容和回答人为空，状态为 `unanswered`；Owner 回答后写入回答内容、回答人和回答时间，并将状态改为 `answered`。V1 不支持多轮回答，因此不拆分 Question 与 Answer 表。

### 4.2 对象关系

- 一个 User 可以拥有多个 Session；
- 一个 Owner 可以创建多个 Post；
- 一个 Family 或 Owner 可以提出多个 QA；
- 一个 Owner 可以回答多个 QA，未回答 QA 暂时没有回答人；
- 一个 Owner 可以创建多个 Expenditure；
- User 的角色限制由 Service 校验，普通外键本身不能保证关联用户一定是 Owner 或 Family。

User 不通过 V1 页面删除。需要停止某个账号使用时，将账号状态设为不可用，并使其 Session 失效。V1 明确允许删除的 Post 和 Expenditure 使用硬删除；QA 在 V1 不提供删除能力。

### 4.3 数据表大框架

所有主键使用应用生成的 UUID。除明确标记可空的字段外，其余字段均为 `NOT NULL`。`created_at` 默认当前 UTC 时间，`updated_at` 在创建时赋值并由应用在修改时更新。

**users**

| 字段 | 类型 | 默认值 / 空值 | 约束与索引 |
|---|---|---|---|
| `id` | UUID | 应用生成 | 主键 |
| `login_name` | VARCHAR(100) | 无 | 去除首尾空格并转为小写；唯一索引 |
| `display_name` | VARCHAR(80) | 无 | 去除首尾空格；长度 1 至 80 |
| `role` | VARCHAR(20) | 无 | CHECK：`family`、`owner` |
| `password_hash` | VARCHAR(255) | 无 | 只保存 Argon2id 哈希 |
| `status` | VARCHAR(20) | `active` | CHECK：`active`、`inactive` |
| `created_at` | TIMESTAMPTZ | 当前时间 | 以 UTC 保存 |
| `updated_at` | TIMESTAMPTZ | 当前时间 | 以 UTC 保存 |

**sessions**

| 字段 | 类型 | 默认值 / 空值 | 约束与索引 |
|---|---|---|---|
| `id` | UUID | 应用生成 | 主键 |
| `user_id` | UUID | 无 | 外键 `users.id`，删除 User 时 CASCADE；普通索引 |
| `token_hash` | CHAR(64) | 无 | SHA-256 十六进制摘要；唯一索引 |
| `created_at` | TIMESTAMPTZ | 当前时间 | 以 UTC 保存 |
| `expires_at` | TIMESTAMPTZ | 创建时间后 30 天 | 普通索引；过期 Session 不再有效 |

**posts**

| 字段 | 类型 | 默认值 / 空值 | 约束与索引 |
|---|---|---|---|
| `id` | UUID | 应用生成 | 主键 |
| `author_id` | UUID | 无 | 外键 `users.id`，删除 User 时 RESTRICT |
| `title` | VARCHAR(120) | 无 | 长度 1 至 120 |
| `body` | TEXT | 无 | 长度 1 至 10,000 |
| `visibility` | VARCHAR(20) | `family` | CHECK：`public`、`family` |
| `created_at` | TIMESTAMPTZ | 当前时间 | 与 `visibility` 组成倒序列表索引 |
| `updated_at` | TIMESTAMPTZ | 当前时间 | 以 UTC 保存 |

**qas**

| 字段 | 类型 | 默认值 / 空值 | 约束与索引 |
|---|---|---|---|
| `id` | UUID | 应用生成 | 主键 |
| `asked_by` | UUID | 无 | 外键 `users.id`，删除 User 时 RESTRICT |
| `question` | TEXT | 无 | 长度 1 至 2,000 |
| `answer` | TEXT | 可空 | 非空时长度 1 至 10,000 |
| `answered_by` | UUID | 可空 | 外键 `users.id`，删除 User 时 RESTRICT |
| `status` | VARCHAR(20) | `unanswered` | CHECK：`unanswered`、`answered`；与 `created_at` 组成倒序列表索引 |
| `answered_at` | TIMESTAMPTZ | 可空 | 以 UTC 保存 |
| `created_at` | TIMESTAMPTZ | 当前时间 | 以 UTC 保存 |
| `updated_at` | TIMESTAMPTZ | 当前时间 | 以 UTC 保存 |

**expenditures**

| 字段 | 类型 | 默认值 / 空值 | 约束与索引 |
|---|---|---|---|
| `id` | UUID | 应用生成 | 主键 |
| `created_by` | UUID | 无 | 外键 `users.id`，删除 User 时 RESTRICT |
| `spent_on` | DATE | 无 | 倒序列表索引 |
| `amount` | NUMERIC(18,4) | 无 | CHECK：金额大于 0 |
| `currency` | CHAR(3) | 无 | 大写 ISO 4217 三字母代码，由应用校验 |
| `category` | VARCHAR(80) | 无 | V1 使用自由文本；长度 1 至 80 |
| `description` | TEXT | 无 | 长度 1 至 2,000 |
| `created_at` | TIMESTAMPTZ | 当前时间 | 以 UTC 保存 |
| `updated_at` | TIMESTAMPTZ | 当前时间 | 以 UTC 保存 |

所有时间点统一以 UTC 保存，前端按 `APP_TIMEZONE` 配置转换后展示。实际支出日期是业务日期，不因时区转换而改变。

金额使用 PostgreSQL `NUMERIC(18,4)`，不能使用浮点数。币种独立保存为 ISO 4217 三字母代码，例如 `CNY`、`JPY` 或 `USD`，不与金额拼接为字符串。

QA 在 Service 和数据库两层保持状态一致：`unanswered` 时 `answer`、`answered_by`、`answered_at` 必须全部为空；`answered` 时这三个字段必须全部非空。数据库通过 CHECK 约束阻止不完整的回答状态进入持久化数据。

事务由 Service 层控制。一个完整业务动作在同一个事务中完成，Repository 负责执行查询和写入，但不自行提交事务。

### 4.4 状态与枚举

| 枚举 | V1 值 | 用途 |
|---|---|---|
| `UserRole` | `family`、`owner` | 决定登录用户的角色权限 |
| `AccountStatus` | `active`、`inactive` | 决定账号是否允许登录和继续使用 Session |
| `PostVisibility` | `public`、`family` | 决定 Post 对 Public 是否可见 |
| `QAStatus` | `unanswered`、`answered` | 表示 QA 是否已有回答 |
| `CurrencyCode` | ISO 4217 三字母代码 | 表示支出币种，不限定为单一币种 |

角色、状态和可见范围使用字符串字段保存，同时在 Python 应用中定义枚举，并在数据库中添加 CHECK 约束。V1 不使用 PostgreSQL 原生 ENUM，以降低后续调整值域时的迁移复杂度。

### 4.5 ER 图

下图表达 V1 核心数据表及主要关系。字段只保留架构阶段需要确定的内容，不展开数据库长度、默认值和全部索引。
![[Pasted image 20260713184405.png]]

## 5. API 大框架

### 5.1 API 通用约定

FastAPI 对外提供 REST 风格 JSON API，统一使用 `/api/v1` 前缀。路径以复数资源名为主，例如 `/posts`、`/qas` 和 `/expenditures`；单条资源通过 UUID 标识。

生产环境只允许通过 HTTPS 访问 API。浏览器自动携带 Session Cookie，创建、修改和删除请求还必须在请求头中携带 CSRF Token。FastAPI 在进入业务处理前完成会话和 CSRF 校验。

API 数据遵循以下约定：

- 时间点使用 ISO 8601 UTC 格式，业务日期使用 `YYYY-MM-DD`；
- 金额以最多四位小数的十进制字符串传输，例如 `"1000.00"`，避免 JavaScript 浮点精度问题；
- 币种使用 ISO 4217 三字母代码，例如 `JPY`；
- 更新操作使用 `PATCH`，只提交需要修改的字段；
- 删除成功返回 `204 No Content`；
- 列表默认按时间倒序，并使用 `offset` 和 `limit` 分页；`limit` 默认 20、最大 100；
- 分页响应统一包含 `items`、`total`、`offset` 和 `limit`；
- FastAPI 自动生成的 OpenAPI 文档作为开发和联调参考。

公开 Post 与登录后的 Post 使用不同读取路径。`/public/posts` 永远只返回公开内容；`/posts` 只允许 Family 和 Owner 访问。这样可以让公开数据边界更清楚，也能降低缓存配置错误造成家庭内容泄露的风险。

API 错误统一包含错误代码、用户可读信息、字段错误和请求标识，大框架如下：

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "用户可读的错误说明",
    "field_errors": [],
    "request_id": "请求标识"
  }
}
```

FastAPI 中间件为每个请求生成 UUID 请求标识，并将其写入响应和服务端日志；错误响应通过 `request_id` 返回该标识，便于定位同一次请求的日志。

主要 HTTP 状态码包括：`400` 请求不合法、`401` 未登录或 Session 失效、`403` 角色不允许执行操作、`404` 资源不存在或当前用户不可见、`409` 当前状态与操作冲突、`422` 字段校验失败、`429` 请求频率超过限制。

### 5.2 Auth API

| 方法 | 路径 | 权限 | 用途 |
|---|---|---|---|
| `GET` | `/api/v1/auth/csrf` | Public | 签发配对的 CSRF Cookie 和请求头 Token |
| `POST` | `/api/v1/auth/login` | Public | 校验账号密码，创建 Session 并设置 Cookie |
| `POST` | `/api/v1/auth/logout` | Family、Owner | 删除当前 Session 并清除 Cookie |
| `GET` | `/api/v1/auth/me` | Family、Owner | 返回当前用户标识、显示名称和角色 |

V1 不提供注册、邀请、忘记密码、自助改密和用户管理 API。账号创建与密码重置通过服务器脚本完成。

登录请求必须通过 CSRF 与 `Origin` 校验。登录失败时使用统一提示，不区分“账号不存在”和“密码错误”，避免向外部暴露有效账号。`/auth/me` 只返回页面显示和权限判断需要的用户信息，不返回密码哈希、Session 凭证等敏感字段。

### 5.3 Post API

| 方法 | 路径 | 权限 | 用途 |
|---|---|---|---|
| `GET` | `/api/v1/public/posts` | Public | 分页获取公开 Post |
| `GET` | `/api/v1/public/posts/{post_id}` | Public | 查看单条公开 Post |
| `GET` | `/api/v1/posts` | Family、Owner | 分页获取公开和仅家人可见的 Post |
| `GET` | `/api/v1/posts/{post_id}` | Family、Owner | 查看权限范围内的单条 Post |
| `POST` | `/api/v1/posts` | Owner | 创建 Post |
| `PATCH` | `/api/v1/posts/{post_id}` | Owner | 修改 Post |
| `DELETE` | `/api/v1/posts/{post_id}` | Owner | 硬删除 Post |

创建和修改 Post 时，FastAPI 校验标题、正文和可见范围。Public 接口的 Repository 查询必须固定包含 `visibility = public` 条件，不能依赖前端过滤。

### 5.4 QA API

| 方法 | 路径 | 权限 | 用途 |
|---|---|---|---|
| `GET` | `/api/v1/qas` | Family、Owner | 分页获取家庭 QA |
| `GET` | `/api/v1/qas/{qa_id}` | Family、Owner | 查看单条 QA |
| `POST` | `/api/v1/qas` | Family、Owner | 提交问题，初始状态为 `unanswered` |
| `PUT` | `/api/v1/qas/{qa_id}/answer` | Owner | 新增或替换该问题的一次回答，并更新为 `answered` |

QA 不提供 Public API。Family 和 Owner 可以查看全部家庭 QA，也可以提交问题，但不能回答或修改状态。Owner 回答时由 Service 在同一事务中写入回答内容、回答人、回答时间和状态。

V1 不提供多轮回答、私密问题、归档和删除 QA 的 API。

### 5.5 Expenditure API

| 方法 | 路径 | 权限 | 用途 |
|---|---|---|---|
| `GET` | `/api/v1/expenditures` | Family、Owner | 分页获取重大支出记录 |
| `GET` | `/api/v1/expenditures/{expenditure_id}` | Family、Owner | 查看单条重大支出记录 |
| `POST` | `/api/v1/expenditures` | Owner | 创建重大支出记录 |
| `PATCH` | `/api/v1/expenditures/{expenditure_id}` | Owner | 修改重大支出记录 |
| `DELETE` | `/api/v1/expenditures/{expenditure_id}` | Owner | 硬删除重大支出记录 |

Expenditure 不提供 Public API，也不设置单条可见范围。创建和修改时必须校验金额大于零、币种代码合法，并限制说明中只保存支出事项所需的信息。

### 5.6 Dashboard API

| 方法 | 路径 | 权限 | 用途 |
|---|---|---|---|
| `GET` | `/api/v1/dashboard` | Family、Owner | 聚合返回最近的 Post、QA 和 Expenditure |

Dashboard API 调用 Post、QA 和 Expenditure 模块公开的 Service，不直接访问其他模块的 Repository。它只读取和组合已有数据，不创建 Dashboard 表，也不保存聚合结果。

响应只包含各模块最近 5 条记录和必要数量信息，不返回 Next.js 页面路径。页面跳转关系由 Next.js 维护。Public 不能访问 Dashboard API。

## 6. 页面与路由

### 6.1 公共页面

公共页面不要求登录，Public、Family 和 Owner 都可以访问。公开页面由 Next.js 服务端读取公开 API，保证首屏内容完整，同时只使用 `/api/v1/public/posts` 中的数据。

| 路径 | 页面 | 主要内容 |
|---|---|---|
| `/` | Public Home | 项目介绍、最近公开 Post、公开 Post 入口 |
| `/posts` | 公开 Post 列表 | 按时间倒序展示公开 Post，支持分页 |
| `/posts/[postId]` | 公开 Post 详情 | 展示一条公开 Post |
| `/login` | 登录页 | Family 和 Owner 登录入口 |

公开页面不得请求或展示仅家人可见 Post、QA 和 Expenditure。已登录用户仍可访问公开页面；访问 `/login` 时，如果已有有效 Session，则根据角色进入 `/family` 或 `/owner`。

### 6.2 Family 页面

Family 页面位于 `/family/*`，允许 Family 和 Owner 访问。登录后的交互页面通过同域 API 获取数据，FastAPI 仍然负责最终权限判断。

| 路径 | 页面 | 主要内容 |
|---|---|---|
| `/family` | Dashboard | 最近 Post、最近 QA、最近 Expenditure |
| `/family/posts` | Post 列表 | 公开和仅家人可见的 Post |
| `/family/posts/[postId]` | Post 详情 | 权限范围内的一条 Post |
| `/family/qas` | QA 列表 | 全部家庭 QA 和提问入口 |
| `/family/qas/new` | 提问页 | Family 或 Owner 提交一个新问题 |
| `/family/qas/[qaId]` | QA 详情 | 问题、提问人、状态和回答 |
| `/family/expenditures` | Expenditure 列表 | 重大支出记录 |
| `/family/expenditures/[expenditureId]` | Expenditure 详情 | 一条重大支出的完整信息 |

Family 区只提供查看和提问操作，不显示 Post、QA 回答和 Expenditure 的管理按钮。Owner 也可以进入 Family 区，以实际阅读视角检查内容和权限结果。

### 6.3 Owner 管理页面

Owner Workspace 位于 `/owner/*`，只允许 Owner 访问。该区域只管理 V1 的 Post、QA 和 Expenditure，不提供用户、角色、系统配置或审计管理页面。

| 路径 | 页面 | 主要内容 |
|---|---|---|
| `/owner` | Owner Workspace | 三个管理模块、提出问题入口和待处理 QA 摘要 |
| `/owner/posts` | Post 管理列表 | 查看并进入创建、编辑、删除操作 |
| `/owner/posts/new` | 新建 Post | 填写标题、正文和可见范围 |
| `/owner/posts/[postId]/edit` | 编辑 Post | 修改或删除指定 Post |
| `/owner/qas` | QA 管理列表 | 查看全部问题和回答状态，并提供提出问题入口 |
| `/owner/qas/[qaId]` | QA 回答页 | 查看问题并新增或修改一次回答 |
| `/owner/expenditures` | Expenditure 管理列表 | 查看并进入创建、编辑、删除操作 |
| `/owner/expenditures/new` | 新建 Expenditure | 填写支出日期、金额、币种、分类和说明 |
| `/owner/expenditures/[expenditureId]/edit` | 编辑 Expenditure | 修改或删除指定支出记录 |

创建或修改成功后，页面返回对应管理列表并显示操作结果。删除属于不可恢复操作，前端必须先要求 Owner 确认，但最终删除权限仍由 FastAPI 校验。

### 6.4 受保护区导航与退出

Family 与 Owner 受保护区域使用一致的导航层级：

- 区域 Layout 常驻一级导航。Family 提供家庭首页、近况、问答和重大支出；Owner 提供管理工作台、近况管理、问答管理和支出管理；
- 一级导航必须标识当前所在模块，并在移动端允许横向浏览，不因标签长度产生页面级横向溢出；
- 列表页在标题前提供指向区域首页的明确返回入口；详情、新建、编辑和回答页在标题或主要内容前提供指向所属列表页的明确返回入口；
- 返回入口使用固定的父级 Next.js 路由，不使用浏览器历史作为唯一返回方式，避免从外部链接、书签或登录页进入后返回到不可预测位置；
- 表单底部的“取消”属于当前表单操作，不能替代页面顶部的层级导航；
- 用户显示名称作为账号菜单入口。退出登录收纳在账号菜单内，使用“退出登录”文字和退出图标，不在每个子页面首屏单独展示只有图标的退出按钮；
- 退出仍然删除服务器端 Session 并清除 Cookie，成功后返回公开首页。调整入口位置只改变交互层级，不改变认证和权限行为。

这种安排将高频的页面移动与低频的会话退出分开：返回和模块切换在页面首屏可见，退出保持可发现但不与返回操作争夺视觉优先级。

### 6.5 页面访问关系

| 页面区域 | Public | Family | Owner |
|---|:---:|:---:|:---:|
| 公共页面 `/`、`/posts/*` | 可以 | 可以 | 可以 |
| 登录页 `/login` | 可以 | 登录后转到 `/family` | 登录后转到 `/owner` |
| Family 区 `/family/*` | 不可以 | 可以 | 可以 |
| Owner 区 `/owner/*` | 不可以 | 不可以 | 可以 |

受保护区域的 Next.js 布局将浏览器 Cookie 转发给 FastAPI `/api/v1/auth/me`，并根据 FastAPI 返回的身份结果执行跳转和页面展示。Next.js 不解析 Session 凭证、不查询 `sessions` 表，也不自行认定用户权限；所有业务数据请求仍由 FastAPI 再次鉴权。具体处理规则如下：

- 未登录访问 `/family/*` 或 `/owner/*` 时，跳转到 `/login`，并保留原目标路径；
- Family 访问 `/owner/*` 时显示无权限页面，不用普通跳转掩盖权限错误；
- Session 过期时清除前端登录状态并返回登录页；
- 资源不存在或当前用户不可见时显示统一的未找到页面；
- Family 登录成功后进入 `/family`，Owner 登录成功后进入 `/owner`；
- 退出登录成功后返回公开首页。

下图表示主要页面区域和用户的核心移动方向，不展开列表分页、表单校验和弹窗等界面细节。

![[Pasted image 20260714185932.png]]


## 7. 关键业务流程

关键业务流程统一经过 Next.js、FastAPI Router、Service、Repository 和 PostgreSQL。Router 负责接收请求和识别当前用户，Service 负责权限、业务规则和事务，Repository 只负责数据操作。

流程中出现未登录、无权限、字段错误或资源不可见时，FastAPI 分别返回统一的 `401`、`403`、`422` 或 `404` 错误，前端负责转换为相应页面提示。

### 7.1 登录流程

用户进入登录页后先取得 CSRF Token，再提交账号和密码。Auth Service 查询 User、验证 Argon2id 密码哈希并创建数据库 Session。成功后，FastAPI 通过 HttpOnly Cookie 返回会话凭证，Next.js 根据角色进入 Family 或 Owner 区域。

![[Pasted image 20260714190404.png]]


登录失败时不创建 Session，并统一提示账号或密码不正确。后续请求从 Cookie 读取随机会话凭证，通过 `sessions` 表取得当前用户；退出登录时删除当前 Session 并清除 Cookie。

### 7.2 Post 发布与查看

Owner 创建、修改或删除 Post 时，Router 先验证 Session 和 CSRF Token，Post Service 再确认 Owner 角色并开启事务。Repository 完成数据操作后，由 Service 提交整个业务事务。

读取 Post 时使用两条明确路径：Public 只能调用公开 API，Family 和 Owner 调用登录 API。Repository 根据调用场景加入可见范围条件，前端不承担数据过滤责任。、

![[Pasted image 20260714190448.png]]


编辑沿用相同的 Owner 权限和事务规则。删除前由前端要求确认，FastAPI 再次校验权限后执行硬删除。

### 7.3 QA 提问与回答

Family 或 Owner 提交问题时，QA Service 创建状态为 `unanswered` 的 QA。Owner 回答时，Service 在同一事务内写入回答内容、回答人、回答时间，并把状态更新为 `answered`。

![[Pasted image 20260714190513.png]]


Family 和 Owner 随后都可以读取已回答内容。Public 无法进入 QA 页面或调用 QA API；V1 不创建第二条回答，也不形成聊天消息流。

### 7.4 Expenditure 记录与查看

Owner 创建或修改 Expenditure 时，Service 校验角色、金额、币种、日期和说明，并在校验通过后提交事务。Family 和 Owner 可以读取支出记录，Public 没有对应页面和 API。

![[Pasted image 20260714190537.png]]


编辑使用相同的校验和事务边界；删除经确认后执行硬删除。支出记录只保存说明所需的信息，不接收银行卡号、完整交易流水号、详细住址或证件信息。

## 8. 项目结构

### 8.1 前后端目录大框架

项目沿用现有的 `eiheizone/backend` 与 `eiheizone/frontend` 两个目录。前后端依赖、构建和运行相互独立，但通过同一套 API 契约协作。

后端采用业务模块内部分层，目录大框架如下：

```text
backend/
├── app/
│   ├── main.py                 # FastAPI 应用入口
│   ├── api.py                  # 汇总并注册各模块 Router
│   ├── core/
│   │   ├── config.py           # 环境配置
│   │   ├── security.py         # 密码、Session、CSRF 公共能力
│   │   └── exceptions.py       # 统一业务异常
│   ├── db/
│   │   ├── base.py             # SQLAlchemy 基础模型
│   │   └── session.py          # 数据库连接与事务 Session
│   └── modules/
│       ├── auth/
│       │   ├── router.py       # 控制层
│       │   ├── schemas.py      # API 输入输出
│       │   ├── service.py      # 认证与会话业务
│       │   ├── repository.py   # User、Session 数据访问
│       │   └── models.py       # User、Session ORM 模型
│       ├── posts/              # 内部同样按 Router、Service、Repository 分层
│       ├── qas/
│       ├── expenditures/
│       └── dashboard/          # 只有 Router、Schema、Service，不建立 ORM 模型
├── alembic/                    # 数据库迁移
├── scripts/
│   ├── create_user.py          # 创建 Family / Owner 账号
│   └── reset_password.py       # 人工重置密码并使旧 Session 失效
├── tests/                      # 按业务模块组织测试
├── pyproject.toml
├── uv.lock
├── .python-version
├── .env.example
└── Dockerfile
```

各业务模块遵循相同依赖方向：

```text
Router -> Service -> Repository -> SQLAlchemy / PostgreSQL
```

`schemas.py` 只定义 API 输入输出，不承担数据库查询；`models.py` 只描述 ORM 持久化结构，不处理 HTTP；事务由 Service 控制。Dashboard 通过其他模块的 Service 读取数据，因此不需要自己的 Repository 和 ORM Model。

前端采用 Next.js App Router，并按 Public、Family、Owner 页面区域组织：

```text
frontend/
├── src/
│   ├── app/
│   │   ├── (public)/
│   │   │   ├── page.tsx                # /
│   │   │   └── posts/                  # /posts/*
│   │   ├── login/page.tsx              # /login
│   │   ├── family/
│   │   │   ├── layout.tsx              # 通过 /auth/me 检查 Family / Owner 身份
│   │   │   ├── page.tsx                # /family
│   │   │   ├── posts/                  # /family/posts/*
│   │   │   ├── qas/                    # /family/qas/*
│   │   │   └── expenditures/           # /family/expenditures/*
│   │   ├── owner/
│   │   │   ├── layout.tsx              # 通过 /auth/me 检查 Owner 身份
│   │   │   ├── page.tsx                # /owner
│   │   │   ├── posts/                  # /owner/posts/*
│   │   │   ├── qas/                    # /owner/qas/*
│   │   │   └── expenditures/           # /owner/expenditures/*
│   │   ├── forbidden/page.tsx
│   │   ├── not-found.tsx
│   │   └── globals.css
│   ├── features/
│   │   ├── auth/                        # 登录和当前用户相关界面逻辑
│   │   ├── posts/
│   │   ├── qas/
│   │   ├── expenditures/
│   │   └── dashboard/
│   ├── components/                      # 跨业务复用的 UI 组件
│   ├── lib/
│   │   └── api/                         # FastAPI 客户端与统一错误处理
│   └── types/                           # 前端共享类型
├── public/                              # 不含家庭隐私数据的静态资源
├── tests/
├── package.json
├── next.config.ts
├── .env.example
└── Dockerfile
```

App Router 目录决定页面和 URL，`features` 目录保存相应业务的可复用界面逻辑。前端不复制 FastAPI 的业务规则，权限和数据合法性仍以 API 结果为准。

### 8.2 配置与环境边界

后端使用集中配置对象读取环境变量，业务模块不能各自直接读取系统环境。前端只允许将确实可以公开的配置声明为 `NEXT_PUBLIC_*`，数据库密码、Session 和 CSRF 密钥不能进入浏览器构建结果。

| 配置类别 | 代表配置 | 说明 |
|---|---|---|
| 应用环境 | `APP_ENV`、`LOG_LEVEL` | 区分本地、测试和生产行为；生产日志级别默认 `INFO` |
| 数据库 | `DATABASE_URL` | 仅 FastAPI 使用 |
| 时间 | `APP_TIMEZONE=Asia/Shanghai` | 初始显示时区；迁居后可通过环境变量改为 `Asia/Tokyo` |
| Session | `pfp_session`、30 天固定有效期、安全属性 | 由 FastAPI 统一管理，V1 不滑动续期 |
| CSRF | 签名密钥、`pfp_csrf` 和安全属性 | 由 FastAPI 签发并校验双提交 Token |
| API 地址 | 浏览器相对路径、服务端内部地址 | 浏览器固定使用 `/api/v1`，Next.js 服务端按环境取得 FastAPI 地址 |
| 站点地址 | 应用公开地址 | 用于安全来源校验和页面链接 |

本地开发使用不提交到版本库的 `.env`，仓库只提交不含真实密钥的 `.env.example`。生产环境的数据库凭证和安全密钥保存在腾讯云 VPS 上受限权限的生产 `.env` 中，不写进代码、Docker 镜像或 Git 仓库。V1 暂不启用异机数据库备份；后续启用时，备份加密密钥必须与备份文件分开保存。

### 8.3 本地与线上运行边界

本地开发时，Next.js 和 FastAPI 分别以开发模式运行，PostgreSQL 使用本机已经安装的服务：

| 组件 | 本地建议 | 访问边界 |
|---|---|---|
| Next.js | `localhost:3000` | 浏览器访问入口 |
| FastAPI | `localhost:8000` | 由 Next.js 开发代理转发 `/api/*` |
| PostgreSQL | 本机服务 `localhost:5432` | 使用独立的开发库和测试库；只供 FastAPI 与本地开发工具连接 |

IDE 可以连接本机 PostgreSQL，用于查看 Schema、执行受控查询和辅助调试；应用仍统一通过后端 `DATABASE_URL` 和 SQLAlchemy 访问数据库，不能把 IDE 连接当作应用的数据访问方式。开发库与测试库必须使用不同数据库名称或独立账号，自动测试不得清理或修改开发数据。

Next.js 开发环境通过 `rewrites` 将浏览器请求的 `/api/*` 转发到 FastAPI。它只解决本地同域入口问题，不在 Next.js 中增加业务逻辑或重复实现 API。

生产环境保持相同的外部路径，由腾讯云首尔 VPS 上的 Caddy 和 Docker Compose 承担运行边界：

| 组件 | 生产运行位置 | 访问边界 |
|---|---|---|
| Caddy | VPS Docker 容器 | 公开 80/443，负责 HTTPS 和路径转发 |
| Next.js | VPS Docker 容器 | 负责页面和前端资源，不直接公开端口 |
| FastAPI | VPS Docker 容器 | 负责认证、权限、业务和数据库访问 |
| PostgreSQL 17 | VPS Docker 容器 + named volume | 不对公网开放，只允许 FastAPI 通过内部网络访问 |
| 数据持久化与备份 | PostgreSQL named volume | V1 依靠同机 Volume 持久化；异机加密备份暂缓，并接受整机损坏时无法恢复历史数据的风险 |

V1 通过 SSH/SCP 上传应用变更，在 VPS 使用 Docker Compose 手工构建和发布。

## 9. 设计验收

### 9.1 完成确认

| 检查项 | 结论 |
|---|---|
| V1 范围 | 与 `01_v1_requirements.md` 一致，未纳入后续版本功能 |
| 权限 | Public、Family、Owner 的页面、API 和数据权限已明确 |
| 对象与数据 | 核心对象、关系、状态、字段、约束和索引已明确 |
| API | 核心端点、访问角色、分页和错误结构已明确 |
| 页面 | Public、Family、Owner 页面区域和访问关系已明确 |
| 软件结构 | 前后端职责、后端模块、分层和依赖方向已明确 |
| 关键流程 | 登录、Post、QA 和 Expenditure 的对象协作与事务边界已明确 |
| 运行边界 | 本地代理与腾讯云 VPS + Docker Compose 生产边界已明确 |

本设计已达到进入任务分解阶段的条件。图片上传、通知、搜索、AI、pgvector、多语言和复杂用户管理等内容仍属于后续版本，不应进入 V1 开发任务。

### 9.2 设计变更规则

本文档是 V1 架构设计的正式依据。后续实现可以调整不影响外部契约的类名、函数名和局部代码组织，但出现以下变化时必须同步更新本文档：

- 修改角色、权限或内容可见范围；
- 修改核心对象、数据库字段、关系或状态；
- 修改公开 API 路径、请求语义或主要响应结构；
- 修改页面区域及其角色访问关系；
- 修改认证方式、模块边界、事务边界或部署形态。

影响整体技术方向、跨模块边界或长期演进方式的重大变更，还应新增 ADR 记录选择、理由和影响。

### 9.3 下一阶段输入

下一阶段以本文档为依据编写 `03_v1_plan.md`。任务分解采用适合个人开发者的线性顺序，覆盖运行环境、Auth、Post、QA、Expenditure、Dashboard、前端页面和系统联调。

每项任务应明确实施内容、学习重点与完成标准。具体数据结构、API、权限和事务边界以本文档为准；类名、方法名、异常处理和测试代码在对应任务实施时落地。最终代码、Pydantic Schema、SQLAlchemy Model、Alembic Migration 和测试是代码级详细设计的实际结果。
