---
id: T007
title: 家庭问答（QA）升级为多回答主题讨论与代问代答
type: feat
status: Accepted
created: "2026-11-11"
updated: "2026-11-11"
branch: feat/007-multi-answer-qa
---

# T007 家庭问答（QA）升级为多回答主题讨论与代问代答

## 1. 背景与目标

现有 QA 模块原本设计为单向“父母提问 -> 站长回答”的 1:1 工单结构，且限制仅 Owner 可作答。但在实际家庭生活中：
1. 父母很少在网页端主动打字提问，通常以电话沟通为主，站长经常需要代为记录；
2. 站长也想向父母请教家庭回忆与生活经验，需要支持双向提问；
3. 一个问题往往需要全家多人共同参与并记录不同视角的回忆，需要支持 1:N 多回答。

本任务将 QA 模块升级为**家庭主题问答（1:N）**，支持全员作答、多条独立回答卡片流展示，并轻量支持「代问」与「代回答」标号。

## 2. 范围与不做事项

### 本次范围

- **数据层重构与平滑迁移**：
  - 新增 `qa_answers` 从表（包含 `id`, `qa_id`, `author_id`, `content`, `is_proxy`, `created_at`, `updated_at`）；
  - `qas` 主表增加 `is_proxy` 布尔字段（默认 `False`，用于标示“代问”）；
  - Alembic 迁移脚本将已有存量问答中的 `answer` 平滑迁移至 `qa_answers` 表作为首条记录（`is_proxy=False`），移除原单一答案字段与排他一致性约束。
- **后端业务与权限平权**：
  - 解除“只有 Owner 能回答”的限制，Family 与 Owner 均可发起提问及作答；
  - 增加回答的创建、修改与删除接口，支持标记 `is_proxy`（代回答）；
  - 调整通知策略：新提问通知全家，新回答通知提问人。
- **前端交互重构**：
  - 提问表单支持勾选「代问」；
  - 列表展示 `[代问]` 标号与回答数；
  - 详情页展示问题及按时间排序的多条回答卡片流（含 `[代回答]` 标号）；
  - 统一追加回答输入框与「代回答」勾选项。

### 不做事项

- 不做强定向或人员排他锁（任何人均可回答）；
- 不做树状复杂楼中楼嵌套回复，保持平铺时序卡片流。

## 3. 验收标准

- [x] Alembic 数据库迁移版本完成（`b2c3d4e5f6a7_multi_answer_qas.py`），存量已有回答无损转入 `qa_answers` 表。
- [x] 后端单元测试覆盖：提问（含代问）、Family/Owner 作答（含代回答）、多回答追加与编辑权限。
- [x] 前端类型检查、组件测试与 Lint 全部通过。
- [x] 界面正确呈现 `[代问]` 和 `[代回答]` 标号，且回答列表按时间顺序清晰展现。

## 4. 方案与技术影响

| 方案 | 取舍 |
| --- | --- |
| 1:N 主题-回答卡片流 | 采用：模型纯粹规范，平滑兼容历史数据，契约清晰，易于维护。 |
| 并入 Posts 评论 | 不选：破坏 QA 独立专题定位与现有路由，且 Posts 语义为日常动态分享。 |

- **接口、数据结构与 Migration**：
  - 新增 `qa_answers` 表，外键级联删除 `qas.id`；
  - `qas` 表增加 `is_proxy: Boolean`；
  - 端点：新增 `POST /qas/{qa_id}/answers`、`PUT /qas/{qa_id}/answers/{answer_id}`、`DELETE /qas/{qa_id}/answers/{answer_id}`。
- **配置、权限或部署影响**：
  - 解除 Owner 专属回答限制，Family 角色拥有提问和作答平权。

## 5. 实施与检查记录

- 分支：`feat/007-multi-answer-qa`
- 本机数据库迁移：
  - 执行 `alembic upgrade head`: PASS（迁移至 `b2c3d4e5f6a7 (head)`，表结构校验正常，`qas` 与 `qa_answers` 字段及索引创建成功）
- 后端检查：
  - `ruff check`: PASS
  - `pytest backend/tests/qas/test_qa_schemas.py`: PASS (13/13 passed)
- 前端优化：
  - 去除说注文案，占位符调整为客观中立的 `输入回答...`，标签精简为 `回答`；
  - 重构回答卡片流，采用独立卡片容器 (`bg-card border-border/70 shadow-xs`)、头像首字母标示与左侧对齐排版，避免空旷表格感；
  - 提问与回答表单的复选框（代问/代回答）与提交按钮整合成紧凑底栏对齐。
- 前端检查：
  - `npm run typecheck`: PASS
  - `npm run lint`: PASS (0 errors)
  - `npm test`: PASS (38/38 test files, 124/124 passed)
  - `npm run build`: PASS (Next.js production build succeeded)

## 6. 遗留风险与后续事项

1. **真实头像与成员档案未联动**：
   - 当前回答卡片使用作者 `display_name` 的首字符作为轻量占位头像，尚未与 `T004` 成员空间（`member_profiles.avatar_image_id`）中的真实用户头像打通。若后续需要统一展示家人上传的照片头像，需扩展问答端点以连表或批量读取成员档案。
2. **生产部署的数据库迁移依赖**：
   - 生产环境发版时，必须先在目标数据库执行 `alembic upgrade head` 完成表结构更新与旧数据无损迁移；未执行迁移前不得提前启动新版后端，否则旧单字段访问会发生 schema 异常。
3. **编辑历史版本追溯**：
   - 当前回答修改直接覆写 `content` 并更新 `updated_at`，未保存历史版本快照。家庭内部场景暂无需复杂的历史回滚，后续若有长期口述校对需求可再按需扩展。
