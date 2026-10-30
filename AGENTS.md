# Repository Guidelines

## Communication

- Answer user questions in Chinese.
- Explain the scope before making modifications, and report the actual results and unverified items upon completion.
- When the user only asks for an explanation, diagnosis, or review, do not modify files.

## Planning

Before writing an implementation plan or editing code for an iteration, decide whether the approach is only a local choice or a lasting technical decision.

- Create `docs/adr/NNNN-kebab-title.md` in the same change when the choice affects more than one module, deployment, a security or data boundary, or would have to be made again by a later iteration. Link the ADR from the iteration document. Start it as `Proposed`, and mark it `Accepted` when the iteration is accepted.
- Keep a choice that stays inside one feature in the iteration document, using prose or a short options table. Do not open an ADR for a local layout, query, or UI decision, and do not use a weighted decision matrix.
- Do not add a parallel `.cursor/rules` file. This file is the instruction to follow while planning.

## Project Structure & Module Organization

The deployable application is split into `backend/` and `frontend/`. FastAPI code lives in `backend/app/`; shared configuration, security, errors, and database setup belong in `core/` and `db/`. Business features live in `modules/` and follow `router -> service -> repository`. Backend tests mirror these domains under `backend/tests/`, and Alembic revisions are stored in `backend/alembic/versions/`.

Next.js routes live in `frontend/src/app/`, domain code in `src/features/`, shared components in `src/components/`, browser tests in `frontend/e2e/`, and static assets in `frontend/public/`. Current engineering documentation is under `docs/`; frozen releases are in `docs/versions/`, while active work is recorded in `docs/iterations/`.

## Build, Test, and Development Commands

Run commands from the repository root:

```powershell
cd backend
uv sync --locked
.\.venv\Scripts\fastapi.exe dev app/main.py
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\ruff.exe check .

cd ..\frontend
npm ci
npm run dev
npm test
npm run lint
npm run typecheck
npm run build
```

Use `frontend/e2e/run-local.ps1` for Playwright workflows. Run migrations and migration tests only against dedicated development or test databases.

## Local Environment Protection

- 默认只修改仓库内已跟踪的源代码、测试、Migration 和文档。不要把本机环境修复当作代码任务的一部分。
- 未经用户明确要求，不得创建、删除、移动、重命名或重建 `backend/.venv`、`frontend/node_modules`、`.idea`、缓存目录、测试临时目录、覆盖率目录、Docker 容器/卷或任何仓库外路径。
- 未经用户明确要求，不得运行 `uv sync`、`uv pip install`、`pip install`、`npm install`、`npm ci`、全局包管理器、系统包管理器或修改 PATH、注册表、IDE 全局设置、Shell 配置和用户目录配置。依赖缺失时先报告，不自动改变环境。
- 不得通过删除缓存、测试临时目录或未跟踪文件来“清理”工作树；只报告权限或残留问题。清理必须得到用户明确授权，并且限定具体路径。
- 不得使用 `git clean`、`git reset`、`git checkout --`、`git restore` 或其他会丢弃工作树内容的命令；不得擅自切换或删除分支。
- 不得修改被 `.gitignore` 忽略的 `.idea`、`.env`、`.venv`、`node_modules`、`.next`、覆盖率和测试产物来解决代码问题。只有用户明确要求修复当前 IDE 项目运行配置时，才允许把该项目配置中的绝对路径改成 `$PROJECT_DIR$` 相对路径；仍不得修改 IDE 全局解释器、全局 SDK、注册表或用户目录配置。
- 后端命令优先使用现有 `backend/.venv/Scripts/python.exe` 和 `backend/.venv/Scripts/ruff.exe`；前端命令优先使用现有 `frontend/node_modules/.bin`。如果路径不存在，只报告并等待用户决定，不自动创建替代环境。
- 测试、构建和迁移命令必须明确目标数据库和输出目录；不得连接生产数据库，不得对开发数据库执行破坏性操作。任何需要修改本机服务、数据库、容器或外部服务器的操作都必须先说明范围并获得用户明确授权。
- 不要为了验证而启动长期驻留服务、后台进程或自动重载进程；需要手动测试时只给出启动命令和项目内的工作目录，除非用户明确要求代理启动并管理服务。

## Coding Style & Naming Conventions

Python uses four spaces, `snake_case` functions and modules, and `PascalCase` classes. Keep authorization, transactions, and business rules in services. TypeScript uses two spaces, `kebab-case` filenames, `PascalCase` components, and `camelCase` values. Follow Ruff, ESLint, and TypeScript checks; avoid introducing a new abstraction when an existing project pattern is sufficient.

## Testing Guidelines

Name Pytest files `test_*.py`, Vitest files `*.test.ts(x)`, and Playwright files `*.spec.ts`. Cover permission boundaries, validation, API contracts, transactions, migrations, and changed UI behavior. Add a regression test for every bug fix. Never run automated tests against production data.

## Commit & Pull Request Guidelines

Use Conventional Commits, for example `feat(posts): add image support`, `fix(auth): reject expired sessions`, or `docs: update iteration workflow`. Keep `main` releasable. Pull requests should summarize behavior, link the issue or iteration document, identify migration or configuration impact, list checks run, and include screenshots for visible UI changes.

### Branch, iteration, and PR naming

- One iteration uses one short-lived branch from the latest `main`.
- Branch names use `<type>/v<version>-<iteration-id>-<kebab-topic>`; allowed types are `feat`, `fix`, `docs`, `test`, `ops`, and `refactor`. Example: `docs/v1.5.1-001-documentation-standardization`.
- Iteration files use `docs/iterations/<version>/NNN-kebab-topic.md` and follow the lightweight template in `docs/iterations/_template.md` (status values: `In Progress`, `Accepted`, `Deferred`; keep optional sections only when applicable).
- PR titles use `<type>(<scope>): <summary> [v<version>-<id>]`. The PR body links the iteration and summarizes scope, migration/configuration/deployment impact, checks run, and remaining risks.
- When an iteration has two or more real implementation options, record the options and the reason for the choice in prose or a short table. Do not require a weighted decision matrix. Follow the Planning section above when the choice needs an ADR.

## Git

Git commands are allowed in this repository. Branch names follow the section above. Use Git carefully:

- Later edits stay on that same branch. Do not open another branch for the same feature, and do not split one change across several branches.
- After that branch is merged, start the next piece of work from `main` on one new branch.
- Status, diff, and log are fine. Commit, push, open a Pull Request, merge, or create a product tag only when the user explicitly asks.
- The author and committer of every commit are Zhang Huanzhi `<zhanghuanzhi520@gmail.com>`. Do not add a `Co-authored-by` trailer for Cursor or any other agent.
- Do not force-push, hard-reset, or rewrite published history unless the user explicitly asks.
- Do not initialize, commit, or push the parent `EiheiZone` directory or `notes/` unless the user explicitly asks.

## Security & Documentation

Never commit `.env` files, credentials, real family data, database dumps, SSH or signing keys, or generated private artifacts. Do not rewrite frozen records in `docs/versions/` for new behavior; record new work in `docs/iterations/`.

## Local Server Access

- 进行已授权的服务器运维时，先读取本机忽略文件 `.local/server-login.md` 获取连接参数；不要反复向用户索要其中已经记录的信息。
- 该文件只保存主机、端口、用户和本机私钥路径，不保存密码、私钥内容或验证码。
- 连接前确认任务范围；优先使用密钥和标准 SSH 端口，必要时再尝试备用端口。
