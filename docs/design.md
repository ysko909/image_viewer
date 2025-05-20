# 要件定義書

## 目的

`app/static/img` ディレクトリに保存されている画像ファイルの一覧をWebページに表示し、各画像をクリックすると専用のページで大きく表示する。

## 機能

- `/images` のようなURLにアクセスすると、画像ファイル一覧ページが表示される。
- ページには、`app/static/img` ディレクトリ内のすべての画像ファイル名がリスト形式で表示される。
- 各ファイル名は、画像表示ページへのリンクとする。
- `/image/<filename>` のようなURLにアクセスすると、指定された画像ファイルが表示されるページが表示される。

## 想定ユーザー

- アプリケーションの管理者または開発者

# 設計書

## 概略設計

- Flaskアプリケーションに `/images` ルートと `/image/<filename>` ルートを追加する。
- `/images` ルートでは、`app/static/img` ディレクトリの内容を読み取り、ファイル名のリストを取得する。
- `/images` ルートは、取得したファイル名のリストを `image_list.html` テンプレートに渡し、画像表示ページへのリンクを含む一覧を生成する。
- `/image/<filename>` ルートでは、指定されたファイル名を `image_display.html` テンプレートに渡し、画像を表示する。

## 機能設計

### ルート `/images`

- HTTPメソッド: GET
- 処理内容:
    1. `app/static/img` ディレクトリのパスを取得する。
    2. 指定されたディレクトリ内のファイル一覧を取得する。
    3. 取得したファイル一覧から、画像ファイル（例: `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp` などの拡張子を持つファイル）をフィルタリングする。
    4. フィルタリングされたファイル名のリストを `image_list.html` テンプレートに渡してレンダリングする。
- レスポンス: 画像ファイル一覧を表示するHTMLページ

### ルート `/image/<filename>`

- HTTPメソッド: GET
- パラメータ: `<filename>` (表示する画像ファイル名)
- 処理内容:
    1. パラメータとして受け取ったファイル名を `image_display.html` テンプレートに渡してレンダリングする。
- レスポンス: 指定された画像ファイルを表示するHTMLページ

### テンプレート `image_list.html`

- ベーステンプレート: `layout.html` を継承する。
- 表示内容:
    - ページタイトル: "画像ファイル一覧"
    - `app/static/img` ディレクトリ内の画像ファイル名をリスト (`<ul>` または `<ol>`) で表示する。
    - 各リスト項目 (`<li>`) は、ファイル名と、画像表示ページへのリンク (`<a>`) を含む。リンクのURLは `/image/<ファイル名>` とする。

### テンプレート `image_display.html`

- ベーステンプレート: `layout.html` を継承する。
- 表示内容:
    - ページタイトル: "画像表示"
    - 指定された画像ファイル (`<img>` タグを使用) を表示する。画像のURLは `/static/img/<ファイル名>` とする。
    - 一覧ページに戻るためのリンク (`<a>`) を含む。

## クラス構成

既存の `app.py` に新しいルート関数を追加する。新しいクラスは不要。

- `app.py`:
    - `index()` 関数 (既存)
    - `image_list()` 関数 (修正): `/images` ルートに対応し、画像ファイル一覧を取得して `image_list.html` をレンダリングする。リンク先を `/image/<filename>` に変更。
    - `image_display()` 関数 (新規): `/image/<filename>` ルートに対応し、指定された画像を表示するために `image_display.html` をレンダリングする。

## ディレクトリ構成

```
/app
├── app.py
├── static/
│   └── img/
│       ├── code_smartphone_qrcode.png
│       ├── kanban_closed.gif
│       └── seiza_fuyu_daisankaku.webp
├── templates/
│   ├── index.html
│   ├── image_display.html (新規作成)
│   └── layout.html
└── docs/
    └── design.md (更新)
```

## テスト計画

- `tests/test_app.py` にテストコードを作成/更新する。
- `/images` ルートへのGETリクエストが成功することを確認するテスト。
- `/images` ページのHTMLに、画像ファイル名と `/image/<filename>` 形式のリンクが含まれていることを確認するテスト。
- `/image/<filename>` ルートへのGETリクエストが成功することを確認するテスト。
- `/image/<filename>` ページのHTMLに、指定した画像ファイルが表示される `<img>` タグが含まれていることを確認するテスト。