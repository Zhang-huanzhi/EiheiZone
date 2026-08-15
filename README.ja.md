# EiheiZone

[English](README.md) | [简体中文](README.zh-CN.md) | 日本語

EiheiZone は、日々の近況共有、家族からの質問への回答、まとまった支出の記録を行うためのプライベートな家族向け情報ポータルです。公開コンテンツ、家族専用エリア、Owner 管理エリアを、1 つのレスポンシブ Web アプリケーションとして提供します。

**現在のバージョン：** v1.1.0。2026 年 8 月 15 日にリリース受け入れが完了しました。対応する Git tag は、リリースコミットのマージと本番検証の成功後に作成します。

**本番サイト：** [https://eihei.zone](https://eihei.zone)

<p align="center">
  <img src="frontend/public/screenshots/login-mobile.png" alt="EiheiZone のモバイルログイン画面" width="280">
</p>

> アプリケーション UI は簡体字中国語です。上記の英語、中国語、日本語は README の翻訳であり、アプリケーションの多言語対応を示すものではありません。

## 機能

- **ロールベースのアクセス制御：** Public、Family、Owner ごとに異なる画面を提供し、バックエンドで権限を強制します。
- **Post：** Family と Owner がテキストまたは画像付きの近況を投稿し、公開範囲を `public` または `family` に設定できます。Owner はすべての Post を管理します。
- **Post 画像：** 1 件あたり最大 9 枚。バックエンドで権限を確認し、WebP に統一して永続メディア volume に保存します。
- **家族 Q&A：** Family と Owner がそれぞれの画面から質問でき、Owner が回答します。一覧には回答時刻も表示します。
- **まとまった支出：** 家族内だけで共有し、金額は正確な十進数、通貨は ISO 4217 コードで保持します。
- **Dashboard：** 独立した Dashboard テーブルを作らず、最近の Post、Q&A、支出を集約します。
- **インストール可能な体験：** レスポンシブ UI、PWA Manifest、本番 HTTPS デプロイを備えます。
- **運用ツール：** Alembic Migration、アカウントとメディアの保守スクリプト、必須 CI、SSH 自動デプロイ、ヘルスチェック、commit 単位のロールバックを提供します。

## ロールと権限

| 操作 | Public | Family | Owner |
| --- | :---: | :---: | :---: |
| 公開 Post の閲覧 | 可 | 可 | 可 |
| 家族限定 Post の閲覧 | 不可 | 可 | 可 |
| テキストまたは画像付き Post の投稿 | 不可 | 可 | 可 |
| 家族向け質問の投稿と閲覧 | 不可 | 可 | 可 |
| まとまった支出の閲覧 | 不可 | 可 | 可 |
| 家族 Dashboard の閲覧 | 不可 | 可 | 可 |
| すべての Post と支出の管理 | 不可 | 不可 | 可 |
| 質問への回答と Owner Workspace の利用 | 不可 | 不可 | 可 |

公開ユーザー登録やユーザー管理画面はありません。信頼された運用者がバックエンドスクリプトでアカウント作成とパスワードリセットを行います。

## アーキテクチャ

```text
ブラウザー / PWA
    |
    v
Caddy（HTTPS とリバースプロキシ）
    |-- ページ要求 --> Next.js 16 / React 19
    `-- /api/* ----> FastAPI
                          |
                          v
                     PostgreSQL
```

ブラウザーは単一のサイト Origin を使用します。Next.js はページと操作を担当し、FastAPI は認証、認可、ビジネスルール、トランザクション、すべてのデータベースアクセスを担当します。バックエンドモジュールは `Router -> Service -> Repository -> PostgreSQL` の構造です。

| 領域 | 技術 |
| --- | --- |
| フロントエンド | Next.js 16、React 19、TypeScript、Tailwind CSS 4、shadcn/ui |
| バックエンド | Python 3.14、FastAPI、Pydantic 2、SQLAlchemy 2 |
| データ | PostgreSQL、Alembic、UUID 主キー、UTC 日時、正確な十進金額 |
| セキュリティ | Argon2id、データベース側 Session、HttpOnly Cookie、署名付き Double Submit CSRF |
| テスト | pytest、Vitest、Testing Library、Playwright |
| デプロイ | Docker Compose、Caddy、HTTPS、コンテナヘルスチェック |

## プロジェクト構成

```text
eiheizone/
|-- .github/workflows/   # CI と本番デプロイ Workflow
|-- backend/
|   |-- alembic/          # データベースマイグレーション
|   |-- app/
|   |   |-- core/         # 設定、セキュリティ、エラー、ページネーション
|   |   |-- db/           # SQLAlchemy Session とモデル登録
|   |   `-- modules/      # Auth、Post、Q&A、Expenditure、Dashboard
|   |-- scripts/          # アカウントおよび E2E 準備ツール
|   `-- tests/            # バックエンドの単体・統合テスト
|-- frontend/
|   |-- e2e/              # Playwright の主要ワークフロー
|   |-- public/           # PWA アイコンとスクリーンショット
|   `-- src/              # App Router ページ、コンポーネント、機能
|-- Caddyfile
|-- docker-compose.yml
`-- deploy.env.example
```

正式ドキュメント：[`docs/README.md`](docs/README.md)。履歴版は [`docs/versions/`](docs/versions/) にあり、[`v1.1.0`](docs/versions/v1.1/) もここに含まれます。進行中の変更は [`docs/iterations/`](docs/iterations/) に記録します。

## ローカルセットアップ

### 必要な環境

- Python 3.14 と [`uv`](https://docs.astral.sh/uv/)
- Node.js 22 と npm
- PostgreSQL 17 以降
- 同梱の E2E ランナーを実行するための PowerShell

開発用とテスト用に分離したデータベースを作成し、アプリケーションロールからアクセスできるようにしてください。例では `eiheizone_dev`、`eiheizone_test`、`eiheizone_app` を使用します。ローカルの PostgreSQL 構成が異なる場合は変更してください。

以下の PowerShell コマンドは、リポジトリルートから実行します。

### 1. バックエンドの設定

```powershell
cd backend
Copy-Item .env.example .env
uv sync --locked
```

続行する前に `backend/.env` を編集します：

- `DATABASE_URL` と `TEST_DATABASE_URL` を別々のデータベースに設定します。
- `CSRF_SECRET` を 32 文字以上のランダムな値に置き換えます。
- 標準のローカルフロントエンドでは `APP_ORIGIN=http://localhost:3000` を維持します。
- `backend/.env` をコミットしないでください。

開発データベースを更新し、最初のアカウントを作成します：

```powershell
.\.venv\Scripts\alembic.exe upgrade head
.\.venv\Scripts\python.exe scripts\create_user.py --prompt-password
```

最初の管理アカウントには `owner` ロールを選択してください。パスワードは対話形式で入力し、信頼できるターミナルだけを使用してください。

### 2. フロントエンドの設定

```powershell
cd ..\frontend
Copy-Item .env.example .env.local
npm ci
```

標準の `BACKEND_API_ORIGIN=http://127.0.0.1:8000` は、以下のバックエンド起動コマンドに対応しています。既存のローカル環境ファイルを上書きしないでください。

### 3. アプリケーションの起動

リポジトリルートから 2 つのターミナルを開きます。

```powershell
cd backend
.\.venv\Scripts\fastapi.exe dev app/main.py --host 127.0.0.1 --port 8000
```

```powershell
cd frontend
npm run dev
```

[http://localhost:3000](http://localhost:3000) を開きます。フロントエンドは同一 Origin の `/api/*` リクエストを FastAPI に転送します。ローカルの OpenAPI ドキュメントは [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) で確認できます。

## アカウントの保守

`backend/` で以下を実行します：

```powershell
# Family または Owner アカウントの作成
.\.venv\Scripts\python.exe scripts\create_user.py --prompt-password

# パスワードをリセットし、そのアカウントの全 Session を無効化
.\.venv\Scripts\python.exe scripts\reset_password.py --prompt-password
```

生成または入力したパスワードはリポジトリに保存されません。初期認証情報はプライベートな手段で共有してください。

## マイグレーションと自動チェック

テストデータベースのマイグレーションでは、必ずテストデータベースを明示的に選択します：

```powershell
cd backend
.\.venv\Scripts\alembic.exe current
.\.venv\Scripts\alembic.exe upgrade head
.\.venv\Scripts\alembic.exe -x database=test current
.\.venv\Scripts\alembic.exe -x database=test upgrade head
```

バックエンドとフロントエンドのチェックを実行します：

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\ruff.exe check .

cd ..\frontend
npm test
npm run lint
npm run typecheck
npm run build
```

テストデータベースのマイグレーション後、ブラウザーの主要ワークフローを実行します：

```powershell
cd frontend
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\e2e\run-local.ps1
```

E2E ランナーは `eiheizone_test` だけを使用し、架空のアカウントを作成して、`3100` と `8100` を一時的に使用します。テストに実際の家族情報や財務情報を使用しないでください。

## 本番デプロイ

本番環境は 1 台の Docker Compose ホストで PostgreSQL 17、FastAPI、Next.js、Caddy を実行します。Pull Request は Backend、Frontend、Deployment artifacts のチェックを通過する必要があります。`main` の CI 成功後、GitHub Actions が固定した SSH host key を使って `/opt/eiheizone/deploy.sh` を呼び出します。スクリプトは fast-forward のみを許可し、完全な commit SHA でイメージを識別し、Compose の準備完了と公開ヘルス API を確認します。

本番 `.env`、デプロイ状態、データベース、メディア volume はサーバー上に保存し、Git には含めません。`rollback.sh` は以前の安定 commit を復元できますが、volume の削除や Alembic Migration の逆実行は行いません。初期設定、ロールバック、画像クリーンアップ、バックアップと復旧の境界は [`docs/operations.md`](docs/operations.md) を参照してください。

## v1.1 の範囲と既知のリスク

- アプリケーション UI は中国語のみで、利用にはネットワーク接続が必要です。家族の実データをオフラインキャッシュしません。
- 登録、招待、セルフサービスのパスワード復旧、Post 画像以外の一般添付、コメント、チャット、通知、検索、AI、完全な家計簿・レポート機能は含まれません。
- 公開済み Post の画像追加・削除・並べ替えは未対応で、孤立画像の清掃は保守スクリプトを手動実行します。
- PostgreSQL と Post 画像は Docker named volume に保存されます。別ホストへの暗号化バックアップと復旧テストは延期されており、ホスト障害でデータを完全に失う可能性があります。
- 利用範囲を拡大する前に、依存関係監査と完全な回帰テストを再実行してください。
- このリポジトリには、本番の秘密情報、実際の家族データ、Android 署名鍵、配布可能な Android パッケージは含まれません。
