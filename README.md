# Image Viewer

PythonのWebフレームワークであるFlaskを使用して作られた、シンプルな画像ビューワーアプリケーションです。指定されたディレクトリ内の画像をWebブラウザで簡単に閲覧できます。

## 主な機能

- **画像一覧表示**: 指定されたフォルダ内の画像ファイルを一覧で表示します。
- **画像個別表示**: 一覧から画像を選択し、個別に表示します。
- **スライドショー**: フォルダ内の画像を自動で切り替えて表示するスライドショー機能です。
  - **設定変更**: スライドショーの表示時間、ループ再生の有無、シャッフル再生の有無を設定ページから変更できます。

## 技術スタック

- **バックエンド**: Python / Flask
- **ライブラリ**: Pillow
- **コンテナ**: Docker / Docker Compose

## セットアップと実行方法

このアプリケーションを実行するには、Dockerを使用する方法（推奨）と、ローカルにPython環境を構築する方法の2通りがあります。

### 1. Dockerを使用する場合 (推奨)

マシンにDockerとDocker Composeがインストールされている必要があります。

1. **Dockerイメージのビルド**

    ```bash
    docker-compose build
    ```

2. **コンテナの起動**

    ```bash
    docker-compose up
    ```

3. **アクセス**

    Webブラウザで `http://localhost:5000` を開きます。

### 2. ローカル環境で実行する場合

1. **リポジトリのクローン**

    ```bash
    git clone <repository-url>
    cd image_viewer
    ```

2. **Python仮想環境の作成と有効化**

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

    *Windowsの場合は `venv\Scripts\activate` を実行してください。*

3. **依存ライブラリのインストール**

    ```bash
    pip install -r requirements.txt
    ```

4. **アプリケーションの起動**

    ```bash
    flask run
    ```

5. **アクセス**

    Webブラウザで `http://localhost:5000` を開きます。

## 設定

アプリケーションの設定は `config.py` ファイルで変更できます。設定ファイルが存在しない場合、`app.py` 内のデフォルト値が使用されます。

- `UPLOAD_FOLDER`: 画像が格納されているディレクトリのパス。
  - デフォルト: `static/img`
- `SLIDESHOW_DURATION`: スライドショーの画像切り替え時間（ミリ秒）。
  - デフォルト: `3000`
- `SLIDESHOW_LOOP`: スライドショーのループ再生を有効にするか。
  - デフォルト: `True`
- `SLIDESHOW_SHUFFLE`: スライドショーのシャッフル再生を有効にするか。
  - デフォルト: `False`

設定を変更するには、プロジェクトルートに `config.py` を作成し、以下のように記述します。

```python
# config.py
UPLOAD_FOLDER = '/path/to/your/images'
SLIDESHOW_DURATION = 5000
```

## プロジェクト構造

```console
.
├── app.py              # Flaskアプリケーションのメインファイル
├── config.py           # (オプション) 設定ファイル
├── Dockerfile          # コンテナビルド用の設定ファイル
├── docker-compose.yml  # Docker Compose用の設定ファイル
├── requirements.txt    # Pythonの依存ライブラリリスト
├── static/             # CSS、JavaScript、画像などの静的ファイル
│   └── img/            # デフォルトの画像保存ディレクトリ
├── templates/          # HTMLテンプレートファイル
│   ├── image_list.html     # 画像一覧ページ
│   ├── image_display.html  # 画像個別表示ページ
│   └── slideshow.html      # スライドショーページ
└── tests/              # テストコード
```
