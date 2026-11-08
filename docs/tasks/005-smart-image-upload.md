---
id: T005
title: 图片上传自适应缩放、多格式兼容与友好中文反馈优化
type: fix
status: Accepted
created: "2026-11-08"
updated: "2026-11-08"
branch: fix/005-smart-image-upload
---

# T005 图片上传自适应缩放、多格式兼容与友好中文反馈优化

## 1. 背景与目标

家庭成员在实际上传照片（如手机拍摄的高清证件照、生活照 `身份证手持.jpg`、多图旅行相册）时，此前会触发 `The uploaded file is not a supported image` 报错，且单次限制 9 张在导入大量照片时极为繁琐。排查发现存在以下五项问题：

1. **后端对高分辨率手机原图一刀切拒绝**：后端内置了 `thumbnail((2048, 2048))` 自动缩放，但在缩放前硬性限制了 `max(width, height) <= 4096` 与总像素 `<= 16M`（1600 万像素）。现代手机相机（24MP / 48MP / 64MP）拍摄的照片极易超过该阈值。
2. **手机双摄 `MPO`（`.jpg`）与常见格式被拒**：iPhone 与主流安卓手机在人像或双摄模式下生成的 `.jpg` 文件内嵌副图，Pillow 识别 `source.format == "MPO"`，而后端仅允许 `{"JPEG", "PNG", "WEBP"}`；同时缺少对 `AVIF`、`GIF`、`BMP`、`TIFF` 的支持。
3. **图库单次批量上传上限过低（原 9 张）**：导入老照片或家庭旅行记录时，单次仅能选 9 张导致需要反复选择很多次。
4. **`members` 模块前端未接入客户端自动预压缩**：直接将数兆、数千像素的原图直传后端；且两端在压缩前均用 5MB 卡死了原始文件大小。
5. **报错信息全英文且笼统**：后端把尺寸超限、格式不支持、苹果 HEIC 改名伪装、文件损坏统一吞并，返回英文 `"The uploaded file is not a supported image"`。

本任务旨在让家庭成员上传照片真正做到**“零心智负担、选图即传”**：支持单次最多批量导入 **299 张**并具备并发提速与实时进度提示；自动兼容并压缩手机高清原图与多格式照片（含 `.jpge`/`.jfif` 变体）；在遇到不兼容文件（如 HEIC）时提供清晰友好的中文指引。

## 2. 范围与不做事项

### 本次范围

- **成员图库大批量上传支持（单次最多 299 张）**：
  - 后端将 `MAX_BATCH_PHOTOS` 提升至 300 张，单批总量上限放宽至 500 MB；
  - 前端抽离 `uploadImagesConcurrently` 控制并发（默认 4 路并发），大幅提升大批量上传效率并避免浏览器卡顿；
  - 实时反馈当前上传进度（`正在上传 (x/total)…`），选图列表优化为折叠摘要展示。
- **后端自适应缩放与多格式兼容（`members` & `posts`）**：
  - 单张原图接收上限从 `5 MB` 提升至 `20 MB`（落盘仍压缩为百 KB 级 WebP）；
  - 防解压炸弹（Decompression Bomb）上限提升至单边 `16384px`、总像素 `7500 万`（覆盖 48MP/50MP/64MP 手机相机原图），在此范围内自动等比缩放到 `2048×2048` 以内；
  - `ALLOWED_FORMATS` 扩充至 `{"JPEG", "MPO", "PNG", "WEBP", "AVIF", "GIF", "BMP", "DIB", "TIFF"}`；
  - 新增 ISOBMFF `ftypheic` / `ftypmif1` 文件头检测，识别伪装成 `.jpg` 的苹果 HEIC 原图并返回专门的中文转换指引；
  - 将所有图片校验报错统一替换为精准中文提示。
- **前端统一智能预压缩与友好提示（`frontend/src/lib/image-upload.ts`）**：
  - 抽离全站通用的 `validateImageFile`、`prepareImageForUpload`、`uploadImagesConcurrently` 与 `formatImageUploadError`；
  - 放行 `.jpge`、`.jfif`、`.jpe` 等常见扩展名；
  - `posts` 与 `members`（个人图库、头像、横幅封面、相册）全部接入客户端 Canvas 2048px WebP 预压缩（环境不支持时平滑回退原图直传）；
  - 文件选择框下方补充清爽的格式与自动压缩说明，报错精确携带文件名。

### 不做事项

- 不引入需要系统级 C 依赖编译的重型第三方解码器（保持容器镜像轻量化与跨平台一致性）；
- 近况动态（Post）继续保持 9 宫格形态不变。

## 3. 验收标准

- [x] 上传长边 `> 4096px`（如 `5000×3500`）的高清照片不再报错，前后端自动等比缩放到 `2048px` 以内并保存为 WebP；
- [x] 上传手机双摄生成的 `MPO`（`.jpg`）以及 `AVIF`、`GIF`、`BMP`、`TIFF`、`.jpge`、`.jfif` 格式图片均能正常转码保存；
- [x] 成员展示空间图库与相册支持单次选择并上传最多 299 张照片，具备 4 路并发处理与实时进度显示（`正在上传 (x/y)…`）；
- [x] 选择或上传 `.heic`（含改后缀名为 `.jpg` 的 HEIC 文件）时，明确返回中文提示：`检测到苹果 HEIC 原图格式，请先在系统相册中导出为 JPG/PNG 后再上传。`；
- [x] 上传区域展示清晰简明的格式与自动压缩说明，单图失败时报错精确指出具体文件名；
- [x] 前后端静态检查、单元测试与生产构建全部通过。

## 4. 实施与检查记录

| 检查 | 结果 | 证据 |
| --- | --- | --- |
| 分支创建 | `PASS` | 从 `main` 切出 `fix/005-smart-image-upload` |
| 后端 Ruff 静态检查 | `PASS` | `.\backend\.venv\Scripts\ruff.exe check backend`（`All checks passed!`） |
| 后端单元测试与集成测试 | `PASS` | `pytest tests\members tests\posts`（`48 passed`） |
| 前端 ESLint 与 TypeScript 类型检查 | `PASS` | `npm --prefix frontend run lint`、`npm --prefix frontend run typecheck` 通过 |
| 前端 Vitest 单元测试与生产构建 | `PASS` | `npm --prefix frontend test -- --run`（`38 passed, 124 passed`）、`npm --prefix frontend run build` 通过 |
