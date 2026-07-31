# EiheiZone

[English](README.md) | [简体中文](README.zh-CN.md) | 日本語

EiheiZone は家族向けの情報共有アプリケーションです。フロントエンドには Next.js、バックエンドには FastAPI を使用し、ローカルの PostgreSQL へのアクセスはすべてバックエンド経由で行います。

## 必要な環境

- Python 3.14 と `uv`
- Node.js 20.9 以降と npm
- 既存の `eiheizone_dev`、`eiheizone_test`、`eiheizone_app` を使用するローカル PostgreSQL
- Docker はフロントエンドとバックエンドのイメージをビルドする場合にのみ使用し、PostgreSQL はホスト上で実行します

## 初回セットアップ

バックエンド：

```powershell
cd backend
Copy-Item .env.example .env
# 既存のローカルデータベースに合わせて .env を変更し、CSRF_SECRET に 32 文字以上のランダムな値を設定します。
uv sync --locked
.\.venv\Scripts\alembic.exe upgrade head
.\.venv\Scripts\python.exe scripts\create_user.py --prompt-password
```

`create_user.py` では、ログイン名、表示名、`family` または `owner` のロールを対話形式で入力します。パスワードはターミナルでのみ入力し、リポジトリには保存しないでください。

フロントエンド：

```powershell
cd ..\frontend
Copy-Item .env.example .env.local
npm ci
```

設定済みの環境では、既存の `.env` や `.env.local` を上書きしないでください。

## ローカルでの起動

2 つのターミナルを開きます。

```powershell
cd backend
.\.venv\Scripts\fastapi.exe dev app/main.py --host 127.0.0.1 --port 8000
```

```powershell
cd frontend
npm run dev
```

ブラウザーで `http://localhost:3000` を開きます。フロントエンドは同一オリジンの `/api` リクエストを `BACKEND_API_ORIGIN` に転送します。バックエンドの `APP_ORIGIN` は、ブラウザーからアクセスするオリジンと一致させてください。

## マイグレーションとチェック

開発データベースのマイグレーション：

```powershell
cd backend
.\.venv\Scripts\alembic.exe current
.\.venv\Scripts\alembic.exe upgrade head
```

テストデータベースは、必ず `-x database=test` を指定して選択します：

```powershell
.\.venv\Scripts\alembic.exe -x database=test current
.\.venv\Scripts\alembic.exe -x database=test upgrade head
```

自動チェック：

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

E2E スクリプトは `eiheizone_test` のみに接続して架空のアカウントを作成し、`3100` と `8100` のポートをその実行で起動したプロセスにのみ使用します。テストには実際の家族情報を使用しないでください。

## オプション：Docker イメージ

PostgreSQL はホスト上で実行します。フロントエンドの API オリジンは、ビルド時に Next.js の rewrites に組み込まれます：

```powershell
docker build -t eiheizone-backend:v1 .\backend
docker build --build-arg BACKEND_API_ORIGIN=http://host.docker.internal:8000 -t eiheizone-frontend:v1 .\frontend
```

イメージの実行時には、実際のローカル設定を環境変数で指定してください。`.env` ファイルやパスワードをイメージにコピーしてはいけません。バックエンドコンテナからホストの PostgreSQL に接続する場合は、`DATABASE_URL` のホストに `host.docker.internal` を使用します。フロントエンドには引き続き `http://localhost:3000` からアクセスします。
