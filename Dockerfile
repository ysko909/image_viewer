# image_viewer/Dockerfile

# --- ベースイメージ ---
# Python 3.10 の軽量版 (Debianベース) を指定します。
# slimイメージはサイズが小さく、arm64 (Apple Silicon) にも対応しています。
FROM python:3.10-slim

# --- 環境変数 ---
# .pycファイルが生成されないようにします (コンテナ環境では不要なことが多い)。
ENV PYTHONDONTWRITEBYTECODE 1
# Pythonのprint()などの出力がバッファされず、即座にログに表示されるようにします。
ENV PYTHONUNBUFFERED 1

# --- 作業ディレクトリ ---
# コンテナ内の作業ディレクトリを作成し、以降の命令の基準パスとします。
WORKDIR /home/app

# システムパッケージの更新とPillowのビルドに必要なものをインストール
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# --- 依存関係のインストール ---
# まず requirements.txt のみをコピーします。
# これにより、ソースコードが変更されても requirements.txt が変更されていなければ、
# この pip install のレイヤーキャッシュが効き、ビルドが高速化されます。
COPY requirements.txt .

# pipを最新版にアップグレードし、requirements.txt に基づいてライブラリをインストールします。
# --no-cache-dir オプションでキャッシュを使わず、イメージサイズを少しでも小さくします。
# 必要なシステムパッケージをインストール
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# --- アプリケーションコードのコピー ---
# プロジェクトのファイルを作業ディレクトリにコピーします。
# (.dockerignore で指定されたファイルは除外されます)
COPY . .

# --- ポートの公開 ---
# Flask アプリケーションがデフォルトで使用するポート 5000 をコンテナ外に公開します。
# (実際にホストOSからアクセスするには docker-compose.yml でのマッピングが必要です)
EXPOSE 5000

# --- コンテナ起動時のコマンド ---
# コンテナが起動したときに実行されるデフォルトのコマンドです。
# Flask の開発サーバーを起動し、コンテナ外からのアクセスを受け付けるために --host=0.0.0.0 を指定します。
CMD ["flask", "run", "--host=0.0.0.0"]
