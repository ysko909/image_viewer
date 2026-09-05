# AGENTS.md

このリポジトリで作業するすべてのAIエージェント（Codex, Claude, Copilot, Cline, Antigravity等）に対する開発ガイドラインおよびプロジェクト仕様書です。

---

## 1. プロジェクト概要

Flaskを使用した軽量なWeb画像・動画ビューワー兼スライドショーアプリケーションです。  
指定フォルダ内のメディアファイルを一覧表示・個別表示・スライドショー再生（カスタム設定・フォルダ選択対応）できます。

### 技術スタック
- **言語**: Python 3.10+
- **Webフレームワーク**: Flask (>=3.0.0, <3.1.0)
- **画像処理**: Pillow (>=10.1.0, <11.0.0)
- **テストフレームワーク**: pytest (>=8.0.0, <9.0.0)
- **コンテナ環境**: Docker / Docker Compose

---

## 2. ディレクトリ構成

```text
.
├── app.py              # Flaskアプリケーションのメインルーティング・ロジック
├── config.py           # アプリケーション設定ファイル（オプション）
├── Dockerfile          # コンテナビルド用定義（Python 3.10-slim）
├── docker-compose.yml  # Docker Compose定義（ポート5001:5000マウント等）
├── requirements.txt    # 依存ライブラリ一覧
├── docs/               # 設計書格納ディレクトリ
│   └── design.md       # 要件定義書・詳細設計書
├── static/             # 静的アセット
│   └── img/            # デフォルト画像保存先（動画も可）
├── templates/          # Jinja2 HTMLテンプレート群
│   ├── layout.html             # ベースレイアウト
│   ├── image_list.html         # 画像・フォルダ一覧
│   ├── image_display.html      # 個別表示画面（画像/動画）
│   ├── slideshow.html          # スライドショー画面
│   └── slideshow_config.html   # スライドショー設定画面
└── tests/              # pytestテストスイート
    ├── __init__.py
    └── test_app.py     # アプリケーションテスト
```

---

## 3. コマンドリファレンス

### テスト実行（最重要）
コード変更後は必ずテストを実行し、全テストがパスすることを確認してください。

```bash
# 仮想環境のpytestを実行
.venv/bin/pytest

# または標準のpytestコマンド
pytest
```

### ローカル実行
```bash
# 仮想環境有効化
source .venv/bin/activate  # macOS / Linux
# venv\Scripts\activate   # Windows

# 依存関係インストール
pip install -r requirements.txt

# アプリ起動
flask run
```

### Docker実行
```bash
# ビルド
docker-compose build

# 起動
docker-compose up
```

---

## 4. 開発規約・設計書駆動開発フロー

### 4.1 設計書駆動開発（Design First）
- **新規機能開発時**: `docs/design.md` に以下の内容を作成・更新し、実装前にユーザーに確認・承認を依頼してください。
  - 要件定義書（目的、機能、想定ユーザー）
  - 設計書（概略設計、機能設計、クラス/関数構成、ディレクトリ構成、テスト計画）
- **既存機能修正時**:
  - `docs/design.md` を参照して開発すること。
  - 修正内容に応じて `docs/design.md` を更新すること。
  - 既存の設計書がない場合は作成すること。
- **実装着手前**: 設計書を作成・更新したら、コードを変更する前に必ずユーザーにレビューを依頼してください。

### 4.2 コーディング規約
- **PEP 8準拠**: PythonコードはPEP 8に準拠すること。
- **Docstring**: すべての関数・クラス・モジュールに適切なDocstringを記述すること。
- **完全なコードの提供**: コードの一部を省略（`...` や `// existing code` など）せず、完全な形で提示・修正すること。
- **セキュリティ & ディレクトリトラバーサル防止**:
  - ユーザー入力やパスパラメータを扱う際は、必ず `os.path.normpath` を使用して `UPLOAD_FOLDER` 外への不正アクセスを防止・検証すること。

### 4.3 テスト規約
- 新規機能追加やバグ修正時は、`tests/` 以下に対応するテストコードを追加・更新すること。
- テスト実行（`.venv/bin/pytest`）でエラーが出ないことを確認すること。

---

## 5. Git & Pull Request 運用規律

### 5.1 Git操作
- 操作前に必ず `git status` で状態を確認すること。
- ファイルの移動や削除は `git mv` / `git rm` を使用すること。

### 5.2 Pull Request作成
- 差分を確認した上で、GitHub CLI（`gh pr`）を使用して作成すること。
- PRの概要はプロジェクトのテンプレート等に準拠すること。

### 5.3 Pull Requestレビュー手順
PRレビュー時は以下の手順でファイルごとにコメントを付与すること：
1. PRの差分確認:
   ```bash
   gh pr diff <PR番号>
   ```
2. ファイルごとに行単位でレビューコメントを追加:
   ```bash
   gh api repos/<owner>/<repo>/pulls/<PR番号>/comments \
     -F body="レビューコメント" \
     -F commit_id="$(gh pr view <PR番号> --json headRefOid --jq .headRefOid)" \
     -F path="対象ファイルのパス" \
     -F position=<diffの行番号>
   ```

---

## 6. エージェントの行動規範

- **言語**: コメント・設計書・対話は日本語を基本とすること。
- **事前許可**: ユーザーの明示的な指示または承認なくファイル作成・変更を行わないこと。
- **効率的な報告**: ツール実行時は結果と結論を中心に簡潔に報告すること。
