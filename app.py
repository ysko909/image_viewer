# image_viewer/app.py
import os
import random
from flask import Flask, render_template, url_for, abort, redirect, send_file, Response, request
from PIL import Image

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
# スライドショー対象拡張子 (デフォルトはNone: フォルダ内の全検出拡張子)
app.config.setdefault('SLIDESHOW_EXTENSIONS', None)

# サポートするメディア拡張子定義
SUPPORTED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'svg'}
SUPPORTED_VIDEO_EXTENSIONS = {'mp4', 'webm', 'mov', 'm4v'}
SUPPORTED_MEDIA_EXTENSIONS = SUPPORTED_IMAGE_EXTENSIONS | SUPPORTED_VIDEO_EXTENSIONS

# アップロードフォルダやサムネイルフォルダのパスを設定（デフォルト値）
# config.py で上書き可能
app.config.setdefault('UPLOAD_FOLDER', os.path.join(app.static_folder, 'img'))
app.config.setdefault('THUMBNAIL_FOLDER', os.path.join(app.config['UPLOAD_FOLDER'], 'thumbnails'))
app.config.setdefault('MAX_CONTENT_LENGTH', 16 * 1024 * 1024) # 例: 16MB
app.config.setdefault('ALLOWED_EXTENSIONS', SUPPORTED_MEDIA_EXTENSIONS)
app.config.setdefault('THUMBNAIL_SIZE', (128, 128)) # サムネイルの最大サイズ

def sort_image_files(image_files, sort_by='name_asc'):
    """
    画像ファイルリストを指定された条件でソートする
    """
    img_dir = app.config['UPLOAD_FOLDER']
    if sort_by == 'name_desc':
        return sorted(image_files, reverse=True)
    elif sort_by == 'date_desc':
        def get_mtime(f):
            p = os.path.join(img_dir, f)
            try:
                return os.path.getmtime(p)
            except OSError:
                return 0
        return sorted(image_files, key=get_mtime, reverse=True)
    elif sort_by == 'date_asc':
        def get_mtime(f):
            p = os.path.join(img_dir, f)
            try:
                return os.path.getmtime(p)
            except OSError:
                return 0
        return sorted(image_files, key=get_mtime)
    elif sort_by == 'size_desc':
        def get_size(f):
            p = os.path.join(img_dir, f)
            try:
                return os.path.getsize(p)
            except OSError:
                return 0
        return sorted(image_files, key=get_size, reverse=True)
    elif sort_by == 'size_asc':
        def get_size(f):
            p = os.path.join(img_dir, f)
            try:
                return os.path.getsize(p)
            except OSError:
                return 0
        return sorted(image_files, key=get_size)
    else:
        return sorted(image_files)

def is_video_file(filename):
    """
    ファイル名から動画ファイルかどうかを判定する
    """
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[-1].lower()
    return ext in SUPPORTED_VIDEO_EXTENSIONS

def get_available_extensions():
    """
    UPLOAD_FOLDER配下に実際に存在するメディアファイル（画像・動画）の拡張子一覧（小文字、ソート済みリスト）を返す
    """
    img_dir = app.config['UPLOAD_FOLDER']
    found_extensions = set()
    if not os.path.isdir(img_dir):
        return []

    for root, dirs, files in os.walk(img_dir):
        if 'thumbnails' in dirs:
            dirs.remove('thumbnails')
        for filename in files:
            if '.' in filename:
                ext = filename.rsplit('.', 1)[-1].lower()
                if ext in SUPPORTED_MEDIA_EXTENSIONS:
                    found_extensions.add(ext)

    return sorted(list(found_extensions))

def get_active_slideshow_extensions():
    """
    現在アクティブなスライドショー対象拡張子のセットを返す。
    設定されていない場合はフォルダ内の実在拡張子（存在しない場合は全メディア拡張子）を返す。
    """
    configured = app.config.get('SLIDESHOW_EXTENSIONS')
    if configured:
        return set(configured)
    available = get_available_extensions()
    if available:
        return set(available)
    return set(SUPPORTED_MEDIA_EXTENSIONS)

def get_image_files(target_dirs=None, recursive=True, sort_by='name_asc', extensions=None):
    """
    画像ディレクトリを探索し、指定された（または許可された）拡張子の画像ファイルパスのリストを返す
    パスはUPLOAD_FOLDERからの相対パス
    """
    img_dir = app.config['UPLOAD_FOLDER']
    if extensions is not None:
        target_extensions = {ext.lower() for ext in extensions}
    else:
        target_extensions = app.config['ALLOWED_EXTENSIONS']
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
            for root, dirs, files in os.walk(normalized_path):
                if 'thumbnails' in dirs:
                    dirs.remove('thumbnails')
                for filename in files:
                    if '.' in filename and filename.rsplit('.', 1)[1].lower() in target_extensions:
                        relative_path = os.path.relpath(os.path.join(root, filename), img_dir)
                        image_files.append(relative_path.replace(os.path.sep, '/'))
        else:
            try:
                for filename in os.listdir(normalized_path):
                    if filename == 'thumbnails':
                        continue
                    file_path = os.path.join(normalized_path, filename)
                    if os.path.isfile(file_path):
                        if '.' in filename and filename.rsplit('.', 1)[1].lower() in target_extensions:
                            relative_path = os.path.relpath(file_path, img_dir)
                            image_files.append(relative_path.replace(os.path.sep, '/'))
            except OSError:
                pass

    # 重複排除とソート
    image_files = list(set(image_files))
    return sort_image_files(image_files, sort_by=sort_by)

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

def get_file_info(filename):
    """
    指定されたメディアファイルの詳細情報（サイズ、更新日時、解像度等）を取得する
    """
    from datetime import datetime
    img_dir = app.config['UPLOAD_FOLDER']
    abs_path = os.path.normpath(os.path.join(img_dir, filename))
    if not abs_path.startswith(os.path.normpath(img_dir)) or not os.path.exists(abs_path):
        return None

    stat = os.stat(abs_path)
    size_bytes = stat.st_size
    if size_bytes < 1024:
        formatted_size = f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        formatted_size = f"{size_bytes / 1024:.1f} KB"
    else:
        formatted_size = f"{size_bytes / (1024 * 1024):.2f} MB"

    mtime_dt = datetime.fromtimestamp(stat.st_mtime)
    formatted_mtime = mtime_dt.strftime('%Y-%m-%d %H:%M:%S')

    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    is_video = is_video_file(filename)

    width, height, dimensions_str = None, None, None
    if not is_video:
        try:
            with Image.open(abs_path) as im:
                width, height = im.size
                dimensions_str = f"{width} × {height} px"
        except Exception:
            pass

    return {
        'filename': filename,
        'size_bytes': size_bytes,
        'formatted_size': formatted_size,
        'mtime': stat.st_mtime,
        'formatted_mtime': formatted_mtime,
        'extension': ext.upper(),
        'is_video': is_video,
        'width': width,
        'height': height,
        'dimensions': dimensions_str
    }

@app.route('/images')
def image_list():
    """
    画像ファイル一覧を表示するページ（検索・ソート・ページネーション対応）
    """
    q = request.args.get('q', '').strip()
    sort_by = request.args.get('sort', 'name_asc')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 24, type=int)
    if page < 1:
        page = 1
    if per_page < 1:
        per_page = 24

    all_files = get_image_files(sort_by=sort_by)
    if q:
        filtered_files = [f for f in all_files if q.lower() in f.lower()]
    else:
        filtered_files = all_files

    total_items = len(filtered_files)
    total_pages = max(1, (total_items + per_page - 1) // per_page)
    if page > total_pages and total_items > 0:
        page = total_pages

    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated_files = filtered_files[start_idx:end_idx]
    file_info_map = {f: get_file_info(f) for f in paginated_files}

    pagination = {
        'page': page,
        'per_page': per_page,
        'total_items': total_items,
        'total_pages': total_pages,
        'has_prev': page > 1,
        'has_next': page < total_pages,
        'prev_page': page - 1,
        'next_page': page + 1
    }

    directories = get_directories()
    return render_template(
        'image_list.html',
        image_files=paginated_files,
        file_info_map=file_info_map,
        all_image_count=len(all_files),
        directories=directories,
        pagination=pagination,
        q=q,
        sort=sort_by,
        title='画像ファイル一覧'
    )

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

    file_info = get_file_info(filename)
    return render_template('image_display.html', filename=filename, file_info=file_info, title=f'{filename} - 画像表示')

@app.route('/thumbnail/<path:filename>')
def thumbnail(filename):
    """
    指定された画像・動画ファイルのサムネイルを返却する。
    画像ファイルはPillowを用いて指定サイズに縮小生成しキャッシュする。
    動画ファイルの場合はSVGアイコンを返却する。
    """
    img_dir = app.config['UPLOAD_FOLDER']
    img_path = os.path.normpath(os.path.join(img_dir, filename))

    # ディレクトリトラバーサル防止
    if not img_path.startswith(os.path.normpath(img_dir)):
        abort(404)

    if not os.path.exists(img_path):
        abort(404)

    # 動画ファイル（mp4, webm, mov, m4v等）の場合はSVGプレースホルダーを返却
    if is_video_file(filename):
        ext_upper = filename.rsplit('.', 1)[-1].upper() if '.' in filename else 'VIDEO'
        video_svg = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128" width="128" height="128">'
            '<rect width="128" height="128" rx="8" fill="#2c3e50"/>'
            '<polygon points="48,36 48,92 92,64" fill="#ecf0f1"/>'
            f'<text x="64" y="112" font-size="12" fill="#bdc3c7" text-anchor="middle" font-family="sans-serif">{ext_upper}</text>'
            '</svg>'
        )
        return Response(video_svg, mimetype='image/svg+xml')

    thumb_dir = app.config['THUMBNAIL_FOLDER']
    thumb_path = os.path.normpath(os.path.join(thumb_dir, filename))

    # サムネイルパスのディレクトリトラバーサル防止
    if not thumb_path.startswith(os.path.normpath(thumb_dir)):
        abort(404)

    # キャッシュが存在し、元画像より新しい場合はキャッシュを返却
    if os.path.exists(thumb_path):
        try:
            if os.path.getmtime(thumb_path) >= os.path.getmtime(img_path):
                return send_file(thumb_path)
        except OSError:
            pass

    # サムネイル生成
    try:
        os.makedirs(os.path.dirname(thumb_path), exist_ok=True)
        with Image.open(img_path) as im:
            thumb_size = app.config.get('THUMBNAIL_SIZE', (128, 128))
            im.thumbnail(thumb_size)
            save_format = im.format if im.format else 'PNG'
            im.save(thumb_path, format=save_format)
        return send_file(thumb_path)
    except Exception:
        # Pillowで開けない（ダミーファイル等）場合は元ファイルをそのまま返却
        return send_file(img_path)

@app.route('/slideshow/<path:filename>')
def slideshow(filename):
    """
    画像ファイルのスライドショーを表示するページ
    <path:filename> を使用してサブフォルダ内のファイルに対応
    """
    from flask import flash, redirect, url_for
    img_dir = app.config['UPLOAD_FOLDER']
    img_path = os.path.normpath(os.path.join(img_dir, filename))
    if not img_path.startswith(os.path.normpath(img_dir)) or not os.path.exists(img_path):
        abort(404)

    active_exts = get_active_slideshow_extensions()

    # 開始ファイル自身の拡張子がスライドショー対象かチェック
    file_ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    if file_ext not in active_exts:
        flash(f'拡張子「.{file_ext}」はスライドショー対象外に設定されています。', 'warning')
        return redirect(url_for('image_display', filename=filename))

    image_files = get_image_files(extensions=active_exts)

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
    
    active_exts = get_active_slideshow_extensions()
    image_files = get_image_files(target_dirs=target_dirs, recursive=recursive, extensions=active_exts)
    
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

    available_extensions = get_available_extensions()
    configured_extensions = app.config.get('SLIDESHOW_EXTENSIONS')
    if configured_extensions is None:
        # 初期状態: フォルダ内の全検出拡張子をすべて選択状態とする
        current_extensions = set(available_extensions)
    else:
        current_extensions = set(configured_extensions)

    return render_template(
        'slideshow_config.html', 
        title='スライドショー設定', 
        current_duration=current_duration, 
        current_loop_enabled=current_loop_enabled,
        current_shuffle_enabled=current_shuffle_enabled,
        available_extensions=available_extensions,
        current_extensions=current_extensions
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
            return redirect(url_for('slideshow_config'))
        else:
            app.config['SLIDESHOW_DURATION'] = duration
    except (ValueError, TypeError):
        flash('無効な数値が入力されました。', 'danger')
        return redirect(url_for('slideshow_config'))

    # 拡張子設定の保存とバリデーション
    available_exts = set(get_available_extensions())
    if available_exts:
        selected_exts = request.form.getlist('extensions')
        valid_selected = {ext.lower() for ext in selected_exts if ext.lower() in available_exts}
        if not valid_selected:
            flash('スライドショー対象の拡張子を少なくとも1つ選択してください。', 'warning')
            return redirect(url_for('slideshow_config'))
        app.config['SLIDESHOW_EXTENSIONS'] = valid_selected

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