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
app.config.setdefault('ALLOWED_EXTENSIONS', {'png', 'jpg', 'jpeg', 'gif', 'webp', 'mp4'})
app.config.setdefault('THUMBNAIL_SIZE', (128, 128)) # サムネイルの最大サイズ

# --- ヘルパー関数 ---
def get_image_files(target_dirs=None, recursive=True):
    """
    画像ディレクトリを探索し、許可された拡張子の画像ファイルパスのリストを返す
    パスはUPLOAD_FOLDERからの相対パス
    """
    img_dir = app.config['UPLOAD_FOLDER']
    allowed_extensions = app.config['ALLOWED_EXTENSIONS']
    image_files = []
    
    if not os.path.isdir(img_dir):
        return []

    # target_dirsが指定されていない、または空の場合は、ルート全体を対象とする
    if not target_dirs:
        target_dirs = ['']

    for target_dir in target_dirs:
        # ディレクトリトラバーサル防止のための正規化
        target_abs_path = os.path.join(img_dir, target_dir)
        normalized_path = os.path.normpath(target_abs_path)
        if not normalized_path.startswith(os.path.normpath(img_dir)):
            continue
            
        if not os.path.isdir(normalized_path):
            continue

        if recursive:
            for root, _, files in os.walk(normalized_path):
                for filename in files:
                    if '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions:
                        relative_path = os.path.relpath(os.path.join(root, filename), img_dir)
                        image_files.append(relative_path.replace(os.path.sep, '/'))
        else:
            try:
                for filename in os.listdir(normalized_path):
                    file_path = os.path.join(normalized_path, filename)
                    if os.path.isfile(file_path):
                        if '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions:
                            relative_path = os.path.relpath(file_path, img_dir)
                            image_files.append(relative_path.replace(os.path.sep, '/'))
            except OSError:
                pass

    # 重複排除とソート
    image_files = list(set(image_files))
    image_files.sort()
    return image_files

def get_directories():
    """
    UPLOAD_FOLDER配下にあるディレクトリのリストを返す（相対パス、ルートディレクトリ含む）
    """
    img_dir = app.config['UPLOAD_FOLDER']
    directories = [''] # ルート（直下）を表す空文字
    if not os.path.isdir(img_dir):
        return directories
        
    for root, dirs, _ in os.walk(img_dir):
        for d in dirs:
            if d == 'thumbnails':
                continue
            abs_dir = os.path.join(root, d)
            rel_dir = os.path.relpath(abs_dir, img_dir)
            directories.append(rel_dir.replace(os.path.sep, '/'))
            
    directories.sort()
    return directories

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
    directories = get_directories()
    return render_template('image_list.html', image_files=image_files, directories=directories, title='画像ファイル一覧')

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

@app.route('/slideshow')
def slideshow_custom():
    """
    クエリパラメータで指定されたフォルダ内の画像でスライドショーを実行する
    例: /slideshow?dirs=folder1,folder2&recursive=true
    """
    from flask import request, flash, redirect, url_for
    
    dirs_str = request.args.get('dirs', '')
    target_dirs = [d.strip() for d in dirs_str.split(',') if d.strip()] if dirs_str else []
    
    recursive = request.args.get('recursive', 'true').lower() == 'true'
    
    image_files = get_image_files(target_dirs=target_dirs, recursive=recursive)
    
    if not image_files:
        flash('指定されたフォルダ内に画像ファイルが見つかりませんでした。', 'warning')
        return redirect(url_for('image_list'))
        
    start_index = 0
    
    if app.config.get('SLIDESHOW_SHUFFLE', False):
        random.shuffle(image_files)

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