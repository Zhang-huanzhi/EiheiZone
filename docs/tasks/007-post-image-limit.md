---
id: T007
title: 限制近况动态图片上限为9张并修复九宫格显示
type: fix
status: Accepted
created: "2026-11-09"
updated: "2026-11-09"
branch: fix/007-post-image-limit
---

# T007 限制近况动态图片上限为9张并修复九宫格显示

## 1. 背景与目标

在前期任务（T005 与 T006）中，家庭成员个人展示空间（`members` 模块）被赋予了大批量照片导入与展示能力（单次最多 299/300 张相片导入、并发提速与流式相册）。
然而，**近况动态（`posts` 模块）**属于家庭朋友圈式的日常动态分享，其核心视觉呈现为经典的**“九宫格”**（最多 9 张图片，3×3 矩阵布局）。

当前系统在动态图片处理上存在以下问题：
1. **九宫格列数计算逻辑缺陷**：前端 `PostImages` 针对 3 张图计算列数时命中 `images.length <= 4`，导致 3 张图被渲染为 2 列（第 1 行 2 张，第 2 行 1 张留白），破坏了标准九宫格的视觉平衡（3 张图应当排满一行 3 列）；
2. **九宫格缺少渲染边界切片保护**：`PostImages` 未对图片数组进行切片防御，若传入异常数据可能溢出 9 格破坏信息流布局；
3. **前端动态表单（`PostForm`）选图交互缺少硬拦截**：已有 9 张图时，文件选择框未被禁用；单次选择超出剩余配额时虽有提示但未清空 `input.value`，导致浏览器控件残留已选文件且同名重选失效；
4. **后端提示未完全中文化**：`backend/app/modules/posts/image_service.py` 中的 `attach_images` 与 `replace_post_images` 仍保留英文报错，且前端表单未精确捕获 `INVALID_IMAGE_LIST` 等错误码。

本任务旨在修复九宫格排版缺陷，并在前后端对近况动态严格执行最多 9 张图片的完整防御与友好中文反馈。

## 2. 范围与不做事项

### 本次范围

- **前端九宫格排版与边界修复（`frontend/src/features/posts/post-images.tsx`）**：
  - 修正列数计算：1 张排 1 列，2 张与 4 张排 2 列（4 张为 2×2 田字格），3 张与 5~9 张排 3 列（3 张为 3×1 单行满格）；
  - 增加渲染数量安全切片 `images.slice(0, 9)`，确保组件绝对不溢出九宫格。
- **前端动态表单交互强化（`frontend/src/features/posts/post-form.tsx`）**：
  - 当图片达到 9 张时，文件选择控件自动禁用（`disabled`）并提示已达上限；
  - 超额选择时明确中文警告，并清空重置 `event.target.value = ""`；
  - 补充图片计数指示器 `图片（最多 9 张） 【x / 9】`；
  - 提交逻辑增加防御性校验；
  - 健全服务端 400 错误码捕获（`INVALID_IMAGE_LIST`、`IMAGE_TOTAL_TOO_LARGE` 等），直接呈现精准中文提示。
- **后端报错提示中文化（`backend/app/modules/posts/image_service.py`）**：
  - 统一将动态关联与替换图片的报错信息中文化。
- **完善前后端自动化测试**：
  - 覆盖九宫格列数计算、9 张切片保护、表单超额拦截与禁用、后端关联限制校验。

### 不做事项

- 不调整 `members` 模块的大批量照片导入上限（继续保持 299/300 张）；
- 不改动数据库已有的 `position BETWEEN 0 AND 8` 约束。

## 3. 验收标准

- [x] 查看 3 张图片的动态时，排版为一行 3 列（3×1），不再出现 2 列孤立折行；
- [x] 查看 4 张图片的动态时，排版为 2×2 田字格（2 列）；
- [x] 动态图片展示组件对传入数据执行最大 9 张切片保护；
- [x] 动态编辑/发布表单在已有 9 张图片时，文件选择控件禁用并提示上限；
- [x] 选择图片导致总数超限时，阻断添加并清空文件控件，给出包含当前与新选数量的清晰中文提示；
- [x] 后端动态关联与替换超限或重复时返回规范中文提示；
- [x] 前后端静态检查与自动化测试全部通过。

## 4. 方案与技术影响

- 接口与数据结构：保持现有 `PostCreate` / `PostUpdate` 契约不变，无需数据库 Migration。
- 配置与权限：无新增环境变量，沿用现有 Family 与 Owner 权限。

## 5. 实施与检查记录

| 检查 | 结果 | 证据 |
| --- | --- | --- |
| 分支创建 | `PASS` | 从 `main` 切出 `fix/007-post-image-limit` |
| 后端 Ruff 静态检查 | `PASS` | `.\backend\.venv\Scripts\ruff.exe check backend`（`All checks passed!`） |
| 后端单元测试 | `PASS` | `.\backend\.venv\Scripts\python.exe -m pytest backend/tests/posts/test_post_images.py` 通过 |
| 前端 ESLint 检查 | `PASS` | `npm --prefix frontend run lint` 通过（0 errors, 0 warnings） |
| 前端 TypeScript 类型检查 | `PASS` | `npm --prefix frontend run typecheck` 通过 |
| 前端 Vitest 单元测试 | `PASS` | `npm --prefix frontend test -- --run`（38 passed, 134 passed） |
| 前端生产构建 | `PASS` | `npm --prefix frontend run build` 成功完成 Next.js 生产优化构建 |
