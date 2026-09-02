# Competitive Research (いかりスーパー競合分析レポート自動生成ツール)

いかりスーパーマーケットの経営戦略室向けに、最新の競合店舗動向（新規出店・改装情報など）を自動で調査・分析し、レポートおよび統合ダッシュボードを生成する自動化ツールです。

## 概要

本ツールは、毎日スケジュール実行（cron等）されることで、インターネット上の最新ニュースからいかりスーパー既存店舗周辺（半径2km以内）および関西全域の競合動向を検出し、以下の成果物を自動生成してリポジトリにコミットします。

1. **競合分析レポート** (Markdown形式)
2. **統合ダッシュボードWebページ** (Leaflet地図埋め込み型HTML)
3. **報告用プレゼンテーションスライド** (PowerPoint形式)

---

## 主な機能

### 1. AIと検索グラウンディングを用いた自動調査
- **Gemini API (Google Search Grounding)** を用いて、Google検索の最新ニュースから信頼できる競合情報を調査します。
- **一時的エラー対策 (503 UNAVAILABLE等)**:
  - 待機時間を徐々に延ばす **指数バックオフ**（最大60秒）を導入。
  - `gemini-2.5-flash` の呼び出しが失敗した際、自動的に `gemini-3.6-flash` へ切り替える **モデルフォールバック機能** を搭載し、APIの高負荷状態でもタスクを完遂します。

### 2. 既存店から半径2km以内の判定（エリア制限）
- 既存店舗データベースの位置情報をもとに、新規競合店舗がいかりスーパー既存店舗から半径2.0km以内の競合であるかを自動的に判別します。

### 3. 競合店情報の自動データベース化
- レポートに新しく登場した競合店情報を検知すると、自動的にその店舗の詳細（住所、座標、営業時間、駐車場情報、特徴など）をWebから自動検索・補完し、データベース (`data/stores_db.json`) を自動的に更新・蓄積します。

### 4. 自動タスクランナーとGit連携
- `src/run_daily_report.sh` により、ネットワーク疎通確認、多重起動防止、本日分の生成判定、自動実行、ログ出力、およびGitへの自動コミットまでを一元管理します。

---

## ディレクトリ構成

```text
Competitive research/
├── README.md              # 本ドキュメント
├── auto_runner.log        # 自動実行ログ（Git追跡対象外）
├── last_success.txt       # 最終レポート生成成功日（進捗管理）
├── pyproject.toml         # Pythonプロジェクト定義 (uv)
├── uv.lock / uv.toml      # パッケージ依存関係ロック
├── data/
│   └── stores_db.json     # いかり既存店および競合店舗のデータベース
├── docs/
│   └── competitive_report.md  # アーカイブ用競合レポート
├── templates/
│   └── dashboard_template.html # ダッシュボードWebページ生成用テンプレートHTML
├── src/
│   ├── run_daily_report.sh  # 定期実行用ランナーシェルスクリプト
│   ├── update_report.py     # Gemini APIによるレポート生成スクリプト
│   ├── auto_lookup_competitors.py # 競合店舗情報の自動検索・DB追加スクリプト
│   ├── main.py              # 地図生成、ダッシュボードHTML、PPTX生成を行うメイン処理
│   └── update_store_db.py   # いかりスーパー既存店の最新情報をスクレイピング・更新するツール
└── report/                # レポート成果物専用ディレクトリ (Git管理対象)
    ├── archive/           # 過去日付の成果物アーカイブ
    ├── 202X_XX_XX_competitive_map_within_2km.html
    ├── 202X_XX_XX_competitive_report_within_2km.pptx
    └── ...
```

---

## セットアップと実行方法

### 動作環境
- Windows (WSL / Ubuntu推奨) または Linux
- `uv` (Python パッケージマネージャー)

### 1. 依存関係のインストール
プロジェクトのルートディレクトリで以下を実行し、仮想環境の構築とライブラリのインストールを行います。

```bash
uv sync
```

### 2. 環境変数の設定
`.env.example` をコピーして `.env` を作成し、Gemini APIキーを設定します。

```bash
cp .env.example .env
```

```env
GEMINI_API_KEY=あなたのGemini_APIキー
```

### 3. 定期実行タスクの登録（タスクスケジューラ）
毎日AM 5:00に自動実行されるタスクをWindowsタスクスケジューラに登録します。

**WSL側から登録する場合:**
```bash
bash scripts/register_task.sh
```

**Windows側から登録する場合 (PowerShell / バッチ):**
- `scripts/register_task.bat` をダブルクリック、または PowerShell で `scripts/register_task.ps1` を実行。

※ タスク登録を解除したい場合は、`bash scripts/unregister_task.sh` または `scripts/unregister_task.bat` を実行してください。

### 4. 定期実行タスクの手動テスト
WSL上のタスクランナーを手動実行してテストすることができます。

```bash
bash src/run_daily_report.sh
```
実行ログは `./auto_runner.log` に出力されます。
