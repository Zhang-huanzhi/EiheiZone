# EiheiZone

English | [简体中文](README.zh-CN.md) | [日本語](README.ja.md)

EiheiZone is a family information application. The frontend uses Next.js, the backend uses FastAPI, and all database access goes through the backend to a local PostgreSQL instance.

## Prerequisites

- Python 3.14 and `uv`
- Node.js 20.9 or later and npm
- Local PostgreSQL using the existing `eiheizone_dev`, `eiheizone_test`, and `eiheizone_app`
- Docker is optional and is only used to build the frontend and backend images; PostgreSQL remains on the host

## Initial setup

Backend:

```powershell
cd backend
Copy-Item .env.example .env
# Update .env for the existing local databases and set CSRF_SECRET to a random value of at least 32 characters.
uv sync --locked
.\.venv\Scripts\alembic.exe upgrade head
.\.venv\Scripts\python.exe scripts\create_user.py --prompt-password
```

`create_user.py` prompts for a login name, display name, and the `family` or `owner` role. Enter the password only in the terminal and never store it in the repository.

Frontend:

```powershell
cd ..\frontend
Copy-Item .env.example .env.local
npm ci
```

Do not overwrite an existing `.env` or `.env.local` in an already configured environment.

## Run locally

Open two terminals.

```powershell
cd backend
.\.venv\Scripts\fastapi.exe dev app/main.py --host 127.0.0.1 --port 8000
```

```powershell
cd frontend
npm run dev
```

Open `http://localhost:3000`. The frontend proxies same-origin `/api` requests to `BACKEND_API_ORIGIN`. The backend `APP_ORIGIN` must match the origin used by the browser.

## Migrations and checks

Development database migrations:

```powershell
cd backend
.\.venv\Scripts\alembic.exe current
.\.venv\Scripts\alembic.exe upgrade head
```

Always select the test database explicitly with `-x database=test`:

```powershell
.\.venv\Scripts\alembic.exe -x database=test current
.\.venv\Scripts\alembic.exe -x database=test upgrade head
```

Automated checks:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\ruff.exe check .

cd ..\frontend
npm run lint
npm run typecheck
npm test
npm run build
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\e2e\run-local.ps1
```

The E2E script connects only to `eiheizone_test`, creates synthetic accounts, and uses ports `3100` and `8100` only for the processes started by that run. Do not use real family information in tests.

## Optional: Docker images

PostgreSQL remains on the host. The frontend API origin is included in the Next.js rewrites at build time:

```powershell
docker build -t eiheizone-backend:v1 .\backend
docker build --build-arg BACKEND_API_ORIGIN=http://host.docker.internal:8000 -t eiheizone-frontend:v1 .\frontend
```

Supply the actual local configuration through environment variables when running an image. Never copy `.env` files or passwords into an image. When the backend container connects to PostgreSQL on the host, use `host.docker.internal` as the host in `DATABASE_URL`; continue to access the frontend at `http://localhost:3000`.
