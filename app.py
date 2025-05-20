# image_viewer/app.py
import os
from flask import Flask, render_template, url_for, abort

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
    return render_template('index.html', title='ようこそ')

@app.route('/images')
def image_list():
    """
    画像ファイル一覧を表示するページ
    """
    img_dir = app.config['UPLOAD_FOLDER'] # app/static/img フォルダのパス
    allowed_extensions = app.config['ALLOWED_EXTENSIONS']
    
    # ディレクトリ内のファイル一覧を取得し、許可された拡張子のファイルのみをフィルタリング
    image_files = []
    try:
        for filename in os.listdir(img_dir):
            if '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions:
                image_files.append(filename)
    except FileNotFoundError:
        # ディレクトリが存在しない場合は空のリストを渡す
        pass

    # ファイル名をソート（任意）
    image_files.sort()

    # テンプレートにファイルリストを渡してレンダリング
    return render_template('image_list.html', image_files=image_files, title='画像ファイル一覧')

@app.route('/image/<filename>')
def image_display(filename):
    """
    単一の画像ファイルを表示するページ
    """
    img_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(img_path):
        abort(404) # ファイルが存在しない場合は404エラーを返す

    return render_template('image_display.html', filename=filename)

# --- エラーハンドリングなど（将来追加） ---

# --- アプリケーションの実行 ---
# Docker経由で `flask run` を使うため、以下のブロックは不要
# if __name__ == '__main__':
#     app.run(debug=True) # debug=True は開発時のみ