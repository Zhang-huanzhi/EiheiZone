# V1.3 / 003 完善请求级慢请求监控

| 项目 | 内容 |
| --- | --- |
| 目标版本 | `v1.3` |
| 状态 | In Progress |
| 分支 | `feat/v1.3-003-request-slow-monitoring` |

## 1. 目标

在现有 `X-Request-ID` 和 FastAPI 后端耗时记录基础上，增加默认 `300ms` 的可配置慢请求日志，统一记录请求方法、路径、状态码、耗时、请求 ID 和稳定异常分类，并在慢请求日志中补充数据库查询数量与总耗时。

本迭代只测量 FastAPI 收到请求后的服务端处理时间，不把它解释为用户实际等待时间。

## 2. 本次范围

- 增加 `SLOW_REQUEST_THRESHOLD_MS` 配置，默认值为 `300`；
- 保留 `Request completed`，并在耗时大于等于阈值时增加 `Slow request` 告警；
- 慢请求日志包含 `request_id`、`method`、`path`、`status_code`、`duration_ms`、`exception_category`；
- 异常分类固定为 `none`、`http`、`validation`、`app`、`unhandled`、`cancelled`；
- 通过 SQLAlchemy 引擎事件按请求聚合 `db_query_count` 与 `db_duration_ms`；
- 仅在慢请求日志输出数据库聚合，不记录 SQL 语句、绑定参数或业务数据；
- 增加配置、请求日志、异常分类和 SQL 聚合回归测试。

## 3. 不做事项

- 不新增 HTTP API、数据库表或 Alembic Migration；
- 不修改 Next.js、RSC、Caddy 或浏览器端性能采集；
- 不把 FastAPI 处理时间当作用户端到端等待时间；
- 不在日志中记录 SQL 文本、参数、异常消息或用户数据。

## 4. 技术方案与候选选择

请求中间件为每个请求建立 `RequestMetrics` 上下文，在 `finally` 中统一输出完成日志并清理上下文。错误处理器将分类写入 `request.state`，因此正常响应、统一错误响应和中间件捕获的未处理异常可以共享同一套日志字段。

SQLAlchemy 的 `before_cursor_execute`、`after_cursor_execute` 和 `handle_error` 事件只在请求上下文存在时工作。每次游标执行累加查询次数，并使用单调时钟累计数据库执行时间。取消请求使用日志约定状态码 `499`，实际响应仍由上游连接生命周期决定。

普通完成日志与慢请求告警同时保留，便于兼容现有日志并直接按 `Slow request` 筛选长尾请求。

## 5. 影响范围

| 范围 | 影响 |
| --- | --- |
| FastAPI 请求日志 | 新增慢请求告警和异常分类字段 |
| 数据库观测 | 慢请求增加查询数量和数据库总耗时 |
| 配置 | 新增 `SLOW_REQUEST_THRESHOLD_MS` |
| API、数据库结构 | 无契约和 Migration 变化 |
| 网络与浏览器体验 | 不在本迭代测量或解释范围内 |

## 6. 验收标准

1. 默认阈值为 `300ms`，环境变量可覆盖，非正数配置启动校验失败。
2. 请求耗时小于阈值时不输出 `Slow request`。
3. 请求耗时大于等于阈值时，告警包含请求 ID、方法、路径、状态码、耗时和异常分类。
4. 成功、HTTP 异常、参数校验、AppError、未处理异常和取消请求分别使用稳定分类。
5. 慢请求中的数据库查询数量和总耗时按请求隔离，错误查询也能完成计时，不跨请求残留。
6. 慢请求日志不包含 SQL 文本、绑定参数或异常详情。
7. 后端全量 Pytest 和 Ruff 检查通过。

## 7. 实现与测试记录

| 检查 | 结果 | 证据 |
| --- | --- | --- |
| 配置、请求中间件、异常分类和 SQL 聚合 | 已实现 | `backend/app/core/request_metrics.py`、`backend/app/core/request_id.py`、`backend/app/db/session.py` |
| 请求日志和异常分类测试 | 待验证 | `backend/tests/core/test_request_monitoring.py` |
| SQL 聚合测试 | 待验证 | `backend/tests/core/test_request_monitoring.py` |
| 后端 Pytest | 待验证 | `backend/.venv/Scripts/python.exe -m pytest` |
| Ruff | PASS（初步检查） | `backend/.venv/Scripts/ruff.exe check app tests` |

## 8. 发布记录

本迭代不包含 Migration 或部署拓扑变更。分支、提交、Pull Request、部署和生产日志验收由维护者手动执行并回填。

生产验收应同时记录 FastAPI `duration_ms` 与浏览器端端到端耗时，不能用前者替代网络、Caddy、Next.js、资源下载和浏览器渲染测量。

## 9. 遗留风险

- SQL 聚合只表示数据库驱动执行时间，不包含连接池等待、网络传输或 ORM 对象组装的全部成本；
- 当前请求 ID 仍由 FastAPI 生成，尚未与 Caddy、Next.js 和浏览器的独立观测链路自动关联；
- 生产日志格式化、采集、保留和告警规则仍依赖部署环境，尚未在代码仓库中统一配置。
