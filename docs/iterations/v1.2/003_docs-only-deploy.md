# V1.2 / 003 纯文档变更跳过部署

| 项目 | 内容 |
| --- | --- |
| 目标版本 | v1.2 |
| 状态 | In Progress |
| 分支 | `fix/v1.2-003-docs-only-deploy` |

## 1. 目标

纯 `docs/**` 变更合并到 `main` 后不再重复运行 CI，也不触发生产部署。Pull Request 阶段继续执行 `Backend`、`Frontend`、`Deployment artifacts` 三项 required checks，保证现有合并门禁和分支保护配置不变。

## 2. 本次范围

- 在 `.github/workflows/ci.yml` 的 `push.main` 触发器中忽略 `docs/**`。
- 保留 `pull_request` 触发器及三个 required jobs 的行为。
- 更新当前开发流程、运维说明和迭代索引。

“纯文档变更”严格指一次 push 中所有变更都位于 `docs/**`。只要包含该目录之外的文件，即使同时修改文档，也必须执行完整 CI/CD。

## 3. 不做事项

- 不修改 `.github/workflows/deploy.yml`、部署脚本或生产服务器配置。
- 不跳过 Pull Request 的 required checks，不调整 GitHub 分支保护。
- 不把根目录 `README*.md`、`AGENTS.md` 或其他说明文件纳入忽略范围。
- 不修改应用代码、API、数据库结构或 Migration。

## 4. 技术方案与候选选择

在 `CI` workflow 的 `push` 事件下配置：

```yaml
push:
  branches:
    - main
  paths-ignore:
    - docs/**
```

`pull_request` 不设置路径过滤，因此纯文档 PR 仍会创建并完成三项 required checks，可以在不调整分支保护的情况下合并。

Deploy workflow 继续监听 `CI` 的 `workflow_run`。纯文档变更合并到 `main` 后不会创建 CI run，因此也没有可触发 Deploy 的完成事件。包含任意非 `docs/**` 路径的变更仍按原链路在 CI 成功后部署。

没有选择在整个 CI workflow 上忽略纯文档 PR，因为必需检查若不创建，可能导致分支保护一直等待状态；也没有在 Deploy workflow 内重复计算变更路径，以避免增加两套判定逻辑。

## 5. 影响范围

| 范围 | 影响 |
| --- | --- |
| 纯 `docs/**` Pull Request | 三项 required checks 继续运行 |
| 纯 `docs/**` 合并后的 `main` push | 不运行 CI，不触发 Deploy |
| 包含非 `docs/**` 路径的变更 | 完整 CI/CD 行为不变 |
| 首次实施本迭代的 Pull Request | 因包含 `.github/workflows/ci.yml`，合并后仍会运行 CI/CD |

## 6. 验收标准

1. Workflow YAML 可以解析，`pull_request` 保持无路径过滤。
2. `push` 仍只面向 `main`，并且只忽略 `docs/**`。
3. 三个 required job 的名称、依赖关系和执行内容不变。
4. 纯 `docs/**` PR 可以在三项 required checks 成功后合并。
5. 该 PR 合并后没有新的 `main` CI run，也没有对应的 Deploy run。
6. 包含任意非 `docs/**` 文件的后续变更仍执行完整 CI/CD。

## 7. 实现与测试记录

| 检查 | 结果 | 证据 |
| --- | --- | --- |
| YAML 解析与触发器结构 | PASS | PyYAML `BaseLoader` 解析成功；`pull_request` 无路径过滤，`push` 只匹配 `main` 并忽略 `docs/**` |
| required jobs 保持不变 | PASS | 静态断言三个 job 的 ID、显示名称及 `deployment-artifacts` 依赖关系未变 |
| 纯文档 PR 与合并后触发行为 | 待验证 | 需要在 GitHub 创建并合并后续纯文档 PR |
| 混合或非文档变更触发行为 | 待验证 | 需要后续 GitHub Actions run 作为证据 |

## 8. 发布记录

本迭代不改变运行时代码。首次实施 PR 包含 workflow 配置，合并后会按旧触发边界执行一次完整 CI/CD；新规则从该提交进入 `main` 后生效。

Git 分支、提交、Pull Request、合并和远程 Actions 验证由维护者手动执行并在完成后回填。

## 9. 遗留风险

- GitHub 的真实路径过滤行为无法仅靠本地解析证明，必须通过后续纯文档 PR 验证。
- 根目录 README 和协作说明文件仍会触发部署，这是本迭代明确接受的边界。
- 若未来将构建输入移入 `docs/**`，必须同步收窄或取消该忽略规则。
