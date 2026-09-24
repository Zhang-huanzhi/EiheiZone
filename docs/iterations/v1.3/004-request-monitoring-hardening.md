# V1.3 / 004 请求监控安全加固

| 项目 | 内容 |
| --- | --- |
| 目标版本 | `v1.3` |
| 状态 | Accepted |
| 实现日期 | `2026-09-24` |
| 分支 | `fix/v1.3-004-request-monitoring-hardening` |

## 前言

GitHub Copilot 通过邮件反馈发现请求监控存在高风险的敏感数据日志问题，因此启动本次安全加固。

## 1. 目标

修复请求监控中未处理异常可能把异常文本和 traceback 写入日志的问题，并用真实 PostgreSQL 集成测试验证成功查询、失败查询和跨请求指标隔离。003 的原始迭代文档保持不变，本迭代只记录安全加固与验证范围。

## 2. 本次范围

- 将未处理异常日志改为固定、脱敏的错误消息；
- 不输出 traceback，不传入异常对象；
- 保留 `request_id` 和结构化 `exception_category` 作为排查入口；
- 提取 SQLAlchemy 查询计时事件注册函数，使测试 Engine 复用生产 Engine 的监听器；
- 增加专用 PostgreSQL 数据库上的成功查询、失败查询和请求隔离回归测试；
- 更新迭代索引并新增本迭代记录。

## 3. 不做事项

- 不新增 HTTP API、数据库表或 Alembic Migration；
- 不修改003迭代文档；
- 不记录 SQL 文本、绑定参数、异常消息或业务数据；
- 不使用 SQLite 替代 PostgreSQL 集成覆盖；
- 不改变请求监控字段、异常分类值或慢请求阈值的既有契约。

## 4. 技术方案与候选选择

未处理异常路径使用固定消息调用 `logger.error`，仅传入请求 ID 和 `unhandled` 分类。相比 `logger.exception`，该路径不会自动附加当前异常的 traceback，也不会把异常对象交给日志格式化器。统一完成日志和慢请求日志仍由 `finally` 输出，继续使用003定义的结构化字段。

SQLAlchemy 监听器由 `register_query_monitoring(engine)` 统一注册到生产和测试 Engine。`before_cursor_execute` 创建查询上下文，`after_cursor_execute` 与 `handle_error` 都结束该上下文，因此成功和失败查询都能计时且不会残留未结束记录。

## 5. 影响范围

| 范围 | 影响 |
| --- | --- |
| 未处理异常日志 | 固定脱敏消息，不再包含 traceback 或异常详情 |
| 数据库观测 | 生产与测试 Engine 使用同一套查询计时监听器 |
| API、数据库结构 | 无契约和 Migration 变化 |

## 6. 验收标准

1. 未处理异常日志不包含异常文本、SQL、绑定参数或业务数据。
2. 未处理异常日志不携带 traceback 或异常对象，并保留 `request_id` 与 `exception_category`。
3. PostgreSQL 成功查询被计数并记录耗时。
4. PostgreSQL 失败查询也完成计时，查询上下文无残留。
5. 成功请求和失败请求的查询指标按请求隔离，并出现在慢请求日志中。
6. `TEST_DATABASE_URL` 缺失、目标数据库不是 `eiheizone_test` 或数据库不可用时，测试明确记录环境阻塞，不使用 SQLite 替代。
7. 聚焦测试、后端全量 Pytest 和 Ruff 检查通过。

## 7. 实现与测试记录

| 检查 | 结果 | 证据 |
| --- | --- | --- |
| 未处理异常日志脱敏 | 已实现 | `backend/app/core/request_id.py` 使用固定 `logger.error` 消息 |
| SQLAlchemy 监听器复用 | 已实现 | `backend/app/db/session.py` 的 `register_query_monitoring`；测试 fixture 同样注册 |
| 聚焦监控测试 | PASS | `backend/tests/core/test_request_monitoring.py`，13 passed |
| PostgreSQL 集成覆盖 | PASS | 成功查询、失败查询及请求隔离测试均使用 `TEST_DATABASE_URL` 指向的 `eiheizone_test` |
| 后端全量 Pytest | 部分通过 | `243 passed`；4 个既有图片上传用例在 `tmp_path` fixture setup 阶段因运行环境拒绝扫描临时目录而报错，与本次改动无关 |
| Ruff | PASS | `backend/.venv/Scripts/ruff.exe check .`，`All checks passed!`；有缓存目录访问警告 |

## 8. 遗留风险

- 日志采集器或外层服务器仍可能自行附加上下文，生产环境应继续验证最终落盘内容；
- SQL 聚合仍只表示数据库驱动执行时间，不包含连接池等待、网络传输或 ORM 对象组装的全部成本；
- PostgreSQL 集成测试依赖专用测试库的可用性，环境不可用时只能记录阻塞，不能由 SQLite 替代。
- 当前运行环境的 pytest 临时目录权限导致 4 个既有图片上传用例无法完成 fixture setup；需要在具备临时目录扫描权限的环境补跑全量验收。
