# image_viewer/app.py
import os
from flask import Flask, render_template, url_for, abort, redirect

# Flaskアプリケーションインスタンスを作成
# instance_relative_config=True にすると、インスタンスフォルダから設定を読み込める（今回は使わないが一般的な設定）
app = Flask(__name__, instance_relative_config=True)

# --- 設定 ---
# config.py から設定を読み込む (ファイルが存在しなくてもエラーにならないように silent=True)
app.config.from_pyfile('config.py', silent=True)

# スライドショーのデフォルト表示時間 (ミリ秒)
app.config.setdefault('SLIDESHOW_DURATION', 3000)

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
    トップページを画像一覧ページにリダイレクト
    """
    return redirect(url_for('image_list'))

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

    return render_template('image_display.html', filename=filename, title=f'{filename} - 画像表示')

@app.route('/slideshow/<filename>')
def slideshow(filename):
    """
    画像ファイルのスライドショーを表示するページ
    """
    img_dir = app.config['UPLOAD_FOLDER'] # app/static/img フォルダのパス
    allowed_extensions = app.config['ALLOWED_EXTENSIONS']

    # ディレクトリ内のファイル一覧を取得し、許可された拡張子のファイルのみをフィルタリング
    image_files = []
    try:
        for fname in os.listdir(img_dir):
            if '.' in fname and fname.rsplit('.', 1)[1].lower() in allowed_extensions:
                image_files.append(fname)
    except FileNotFoundError:
        # ディレクトリが存在しない場合は空のリストを渡す
        pass

    # ファイル名をソート（表示順の基本）
    image_files.sort()

    # 開始ファイル名がリストに存在するか確認し、存在しない場合は404エラー
    if filename not in image_files:
        abort(404)

    # 開始ファイル名のインデックスを取得
    start_index = image_files.index(filename)

    # テンプレートにファイルリストと開始インデックスを渡してレンダリング
    # スライドショー表示時間を設定から取得してテンプレートに渡す
    slideshow_duration = app.config.get('SLIDESHOW_DURATION', 3000) # デフォルトは3000ms
    return render_template('slideshow.html', image_files=image_files, start_index=start_index, title='スライドショー', slideshow_duration=slideshow_duration)

@app.route('/slideshow/config', methods=['GET'])
def slideshow_config():
    """
    スライドショー設定ページを表示する
    """
    current_duration = app.config.get('SLIDESHOW_DURATION', 3000)
    return render_template('slideshow_config.html', title='スライドショー設定', current_duration=current_duration)

@app.route('/slideshow/config/save', methods=['POST'])
def save_slideshow_config():
    """
    スライドショー設定を保存する
    """
    from flask import request, redirect, url_for, flash
    try:
        duration = int(request.form['duration'])
        if duration < 500: # 最小値を設定
            flash('表示時間は500ミリ秒以上にしてください。', 'warning')
        else:
            app.config['SLIDESHOW_DURATION'] = duration
            flash('スライドショー表示時間を保存しました。', 'success')
    except ValueError:
        flash('無効な数値が入力されました。', 'danger')
    
    return redirect(url_for('slideshow_config'))

# --- エラーハンドリングなど（将来追加） ---

# --- アプリケーションの実行 ---
# Docker経由で `flask run` を使うため、以下のブロックは不要
# if __name__ == '__main__':
#     app.run(debug=True) # debug=True は開発時のみ