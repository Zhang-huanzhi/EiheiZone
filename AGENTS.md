# Repository Guidelines

## Communication

- Answer user questions in Chinese.
- Explain the scope before making modifications, and report the actual results and unverified items upon completion.
- When the user only asks for an explanation, diagnosis, or review, do not modify files.

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

## Coding Style & Naming Conventions

Python uses four spaces, `snake_case` functions and modules, and `PascalCase` classes. Keep authorization, transactions, and business rules in services. TypeScript uses two spaces, `kebab-case` filenames, `PascalCase` components, and `camelCase` values. Follow Ruff, ESLint, and TypeScript checks; avoid introducing a new abstraction when an existing project pattern is sufficient.

## Testing Guidelines

Name Pytest files `test_*.py`, Vitest files `*.test.ts(x)`, and Playwright files `*.spec.ts`. Cover permission boundaries, validation, API contracts, transactions, migrations, and changed UI behavior. Add a regression test for every bug fix. Never run automated tests against production data.

## Commit & Pull Request Guidelines

Use Conventional Commits, for example `feat(posts): add image support`, `fix(auth): reject expired sessions`, or `docs: update iteration workflow`. Keep `main` releasable. Pull requests should summarize behavior, link the issue or iteration document, identify migration or configuration impact, list checks run, and include screenshots for visible UI changes.

## Git

Git commands are allowed in this repository. Use them carefully:

- One feature or iteration uses one short-lived branch cut from the latest `main`. Name it with `feat/`, `fix/`, or `docs/`, matching the iteration document, for example `docs/v1.4-002-cursor-handoff`.
- Continue later edits on that same branch. Do not open another branch for the same feature, and do not split one change across several branches.
- After that branch is merged, start the next piece of work from `main` on one new branch.
- Status, diff, and log are fine. Commit, push, open a Pull Request, or merge only when the user explicitly asks.
- Do not force-push, hard-reset, or rewrite published history unless the user explicitly asks.
- Do not initialize, commit, or push the parent `EiheiZone` directory or `notes/` unless the user explicitly asks.

## Security & Documentation

Never commit `.env` files, credentials, real family data, database dumps, SSH or signing keys, or generated private artifacts. Do not rewrite frozen V1 history for new behavior; record new work in the relevant iteration document and use an ADR only for durable cross-module decisions.

## Local Server Access

- 进行已授权的服务器运维时，先读取本机忽略文件 `.local/server-login.md` 获取连接参数；不要反复向用户索要其中已经记录的信息。
- 该文件只保存主机、端口、用户和本机私钥路径，不保存密码、私钥内容或验证码。
- 连接前确认任务范围；优先使用密钥和标准 SSH 端口，必要时再尝试备用端口。
