# image_viewer/app.py
import os
import random
from flask import Flask, render_template, url_for, abort, redirect

# Flaskアプリケーションインスタンスを作成
# instance_relative_config=True にすると、インスタンスフォルダから設定を読み込める（今回は使わないが一般的な設定）
app = Flask(__name__, instance_relative_config=True)

# --- 設定 ---
# flash()機能など、セッション管理のためにSECRET_KEYを設定する
# 本番環境では、環境変数などから読み込むべき、より複雑なキーを使用してください
app.config['SECRET_KEY'] = os.urandom(24)

# config.py から設定を読み込む (ファイルが存在しなくてもエラーにならないように silent=True)
app.config.from_pyfile('config.py', silent=True)

# スライドショーのデフォルト表示時間 (ミリ秒)
app.config.setdefault('SLIDESHOW_DURATION', 3000)
# スライドショーのループ設定 (デフォルトは有効)
app.config.setdefault('SLIDESHOW_LOOP', True)
# スライドショーのシャッフル設定 (デフォルトは無効)
app.config.setdefault('SLIDESHOW_SHUFFLE', False)

# アップロードフォルダやサムネイルフォルダのパスを設定（デフォルト値）
# config.py で上書き可能
app.config.setdefault('UPLOAD_FOLDER', os.path.join(app.static_folder, 'img'))
app.config.setdefault('THUMBNAIL_FOLDER', os.path.join(app.config['UPLOAD_FOLDER'], 'thumbnails'))
app.config.setdefault('MAX_CONTENT_LENGTH', 16 * 1024 * 1024) # 例: 16MB
app.config.setdefault('ALLOWED_EXTENSIONS', {'png', 'jpg', 'jpeg', 'gif', 'webp'})
app.config.setdefault('THUMBNAIL_SIZE', (128, 128)) # サムネイルの最大サイズ

# --- ヘルパー関数 ---
def get_image_files():
    """
    画像ディレクトリを再帰的に探索し、許可された拡張子の画像ファイルパスのリストを返す
    パスはUPLOAD_FOLDERからの相対パス
    """
    img_dir = app.config['UPLOAD_FOLDER']
    allowed_extensions = app.config['ALLOWED_EXTENSIONS']
    image_files = []
    
    if not os.path.isdir(img_dir):
        return []

    for root, _, files in os.walk(img_dir):
        for filename in files:
            if '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions:
                # UPLOAD_FOLDERからの相対パスを計算
                relative_path = os.path.relpath(os.path.join(root, filename), img_dir)
                image_files.append(relative_path.replace(os.path.sep, '/')) # パス区切り文字をURL用に'/'に統一
    
    image_files.sort()
    return image_files

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
    image_files = get_image_files()
    return render_template('image_list.html', image_files=image_files, title='画像ファイル一覧')

@app.route('/image/<path:filename>')
def image_display(filename):
    """
    単一の画像ファイルを表示するページ
    <path:filename> を使用してサブフォルダ内のファイルに対応
    """
    # UPLOAD_FOLDER内のファイルかチェック
    img_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    # 正規化して、意図しないディレクトリへのアクセスを防ぐ
    normalized_path = os.path.normpath(img_path)
    if not normalized_path.startswith(os.path.normpath(app.config['UPLOAD_FOLDER'])):
        abort(404)

    if not os.path.exists(img_path):
        abort(404) # ファイルが存在しない場合は404エラーを返す

    return render_template('image_display.html', filename=filename, title=f'{filename} - 画像表示')

@app.route('/slideshow/<path:filename>')
def slideshow(filename):
    """
    画像ファイルのスライドショーを表示するページ
    <path:filename> を使用してサブフォルダ内のファイルに対応
    """
    image_files = get_image_files()

    # 開始ファイル名がリストに存在するか確認し、存在しない場合は404エラー
    if filename not in image_files:
        abort(404)

    # シャッフルが有効な場合、リストを並べ替える
    if app.config.get('SLIDESHOW_SHUFFLE', False):
        # 開始画像をリストの先頭に保持したまま、残りをシャッフルする
        start_image = filename
        image_files.remove(start_image)
        random.shuffle(image_files)
        image_files.insert(0, start_image)

    # 開始ファイル名のインデックスを取得
    start_index = image_files.index(filename)

    # スライドショー表示時間とループ設定を取得してテンプレートに渡す
    slideshow_duration = app.config.get('SLIDESHOW_DURATION', 3000)
    slideshow_loop = app.config.get('SLIDESHOW_LOOP', True)
    return render_template(
        'slideshow.html', 
        image_files=image_files, 
        start_index=start_index, 
        title='スライドショー', 
        slideshow_duration=slideshow_duration,
        slideshow_loop=slideshow_loop
    )

@app.route('/slideshow/config', methods=['GET'])
def slideshow_config():
    """
    スライドショー設定ページを表示する
    """
    current_duration = app.config.get('SLIDESHOW_DURATION', 3000)
    current_loop_enabled = app.config.get('SLIDESHOW_LOOP', True)
    current_shuffle_enabled = app.config.get('SLIDESHOW_SHUFFLE', False)
    return render_template(
        'slideshow_config.html', 
        title='スライドショー設定', 
        current_duration=current_duration, 
        current_loop_enabled=current_loop_enabled,
        current_shuffle_enabled=current_shuffle_enabled
    )

@app.route('/slideshow/config/save', methods=['POST'])
def save_slideshow_config():
    """
    スライドショー設定を保存する
    """
    from flask import request, redirect, url_for, flash
    
    # 表示時間の設定
    try:
        duration = int(request.form.get('duration', 3000))
        if duration < 500: # 最小値を設定
            flash('表示時間は500ミリ秒以上にしてください。', 'warning')
        else:
            app.config['SLIDESHOW_DURATION'] = duration
    except (ValueError, TypeError):
        flash('無効な数値が入力されました。', 'danger')

    # ループ設定の保存
    loop_enabled = 'loop_enabled' in request.form
    app.config['SLIDESHOW_LOOP'] = loop_enabled

    # シャッフル設定の保存
    shuffle_enabled = 'shuffle_enabled' in request.form
    app.config['SLIDESHOW_SHUFFLE'] = shuffle_enabled

    flash('設定を保存しました。', 'success')
    
    return redirect(url_for('slideshow_config'))

# --- エラーハンドリングなど（将来追加） ---

# --- アプリケーションの実行 ---
# Docker経由で `flask run` を使うため、以下のブロックは不要
# if __name__ == '__main__':
#     app.run(debug=True) # debug=True は開発時のみ