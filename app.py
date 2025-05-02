# image_viewer/app.py
import os
from flask import Flask, render_template, url_for

# Flaskアプリケーションインスタンスを作成
# instance_relative_config=True にすると、インスタンスフォルダから設定を読み込める（今回は使わないが一般的な設定）
app = Flask(__name__, instance_relative_config=True)

# --- 設定 ---
# config.py から設定を読み込む (ファイルが存在しなくてもエラーにならないように silent=True)
app.config.from_pyfile('config.py', silent=True)

# アップロードフォルダやサムネイルフォルダのパスを設定（デフォルト値）
# config.py で上書き可能
app.config.setdefault('UPLOAD_FOLDER', os.path.join(app.static_folder, 'img'))
app.config.setdefault('THUMBNAIL_FOLDER', os.path.join(app.config['UPLOAD_FOLDER'], 'thumbnails'))
app.config.setdefault('MAX_CONTENT_LENGTH', 16 * 1024 * 1024) # 例: 16MB
app.config.setdefault('ALLOWED_EXTENSIONS', {'png', 'jpg', 'jpeg', 'gif', 'webp'})
app.config.setdefault('THUMBNAIL_SIZE', (128, 128)) # サムネイルの最大サイズ

# --- ルーティングとビュー関数 ---

@app.route('/')
def index():
    """
    トップページ（将来的にギャラリーページへのリダイレクトまたは直接表示）
    現時点ではシンプルな挨拶を表示
    """
    # return render_template('index.html', title='ようこそ')
    return "<h1>Flask アプリケーション基盤</h1><p>ようこそ！</p>" # ← まずはテンプレートなしで表示確認

# --- エラーハンドリングなど（将来追加） ---

# --- アプリケーションの実行 ---
# Docker経由で `flask run` を使うため、以下のブロックは不要
# if __name__ == '__main__':
#     app.run(debug=True) # debug=True は開発時のみ