# ADR-0002：非运行时文件不触发生产部署

| 项目 | 内容 |
| --- | --- |
| 状态 | Accepted |
| 日期 | 2026-10-30 |
| 相关迭代 | [V1.5.1 / 001 文档标准化与 v1.4 收口](../iterations/v1.5/001-documentation-standardization.md) |

## 背景

v1.2 约定只有纯 `docs/**` 合并才跳过 `main` CI 和生产部署。根目录 README、`AGENTS.md` 和 PR 模板当时被留在部署范围内。这些文件不进入应用镜像的运行逻辑，但一次提交只要包含它们，就会在 CI 成功后执行 `deploy.sh`，重建并发布生产容器。

## 候选方案

1. 维持 v1.2：只有 `docs/**` 跳过部署。README 和代理说明的修改仍会发布生产。
2. 在 `deploy.yml` 里再判断一次变更路径。这样和 `ci.yml` 的 `paths-ignore` 形成两套规则，以后容易不一致。
3. 扩大 `ci.yml` 里 `push.main` 的 `paths-ignore`，把不参与运行的仓库文件一并跳过。Pull Request 仍不设置路径过滤，三项 required checks 保持不变。

## 决策

采用第 3 种。合并到 `main` 时，如果变更全部落在下面这些路径，就不运行 `main` CI，因此也不会触发 Deploy：

- `docs/**`
- `README.md`、`README.zh-CN.md`、`README.ja.md`
- `AGENTS.md`
- `.github/pull_request_template.md`
- `.github/workflows/**`

`frontend/public/screenshots/login-mobile.png` 是 PWA 安装预览图，修改它仍然部署。README 用的工作台截图放在 `docs/_附件_/`，不放进前端公开目录。

## 后果

- 只改文档、README、代理约定、PR 模板或 GitHub workflow 时，生产容器不会重建。
- Workflow 文件合并后就在 `main` 上生效，不需要靠生产部署来加载。Pull Request 仍会运行 Backend、Frontend 和 Deployment artifacts。
- 服务器上的 Git 工作区会暂时停在上一次实际部署的提交，直到下一次运行时代码或部署脚本变更。这与原来的纯 `docs/**` 行为相同。
- 这次规则写在将要合并的 `ci.yml` 里。GitHub 用这次提交中的 workflow 判断路径；当前这些文件都在忽略列表中，所以这次合并本身也不应触发 `main` CI 和 Deploy。该跳过结果还没有在 GitHub 上观察到。
