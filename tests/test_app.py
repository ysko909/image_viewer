import pytest
import os
from app import app

# テストクライアントの設定
@pytest.fixture
def client():
    app.config['TESTING'] = True
    # アプリケーションが使用する実際の画像ディレクトリを使用
    test_img_dir = app.config['UPLOAD_FOLDER']
    os.makedirs(test_img_dir, exist_ok=True)
    
    # このフィクスチャで管理する一意なダミーファイル名
    dummy_filename = 'test_fixture_image.png'
    dummy_image_path = os.path.join(test_img_dir, dummy_filename)
    
    # ダミーファイルを作成
    with open(dummy_image_path, 'w') as f:
        f.write('dummy content')

    with app.test_client() as client:
        yield client

    # テスト後のクリーンアップ
    if os.path.exists(dummy_image_path):
        os.remove(dummy_image_path)


def test_image_list_page(client):
    """
    画像ファイル一覧ページが正しく表示されるかテスト
    """
    response = client.get('/images')
    assert response.status_code == 200
    assert '画像ファイル一覧' in response.data.decode('utf-8')

    # フィクスチャが作成したダミー画像ファイルへのリンクが存在することを確認
    assert b'<a href="/image/test_fixture_image.png">test_fixture_image.png</a>' in response.data

def test_image_display_page(client):
    """
    画像表示ページが正しく表示されるかテスト
    """
    response = client.get('/image/test_fixture_image.png')
    assert response.status_code == 200
    assert b'<img src="/static/img/test_fixture_image.png"' in response.data

    response = client.get('/image/non_existent_image.jpg')
    assert response.status_code == 404

def test_slideshow_page(client):
    """
    スライドショーページが正しく表示されるかテスト
    """
    response = client.get('/slideshow/test_fixture_image.png')
    assert response.status_code == 200
    assert 'スライドショー' in response.data.decode('utf-8')
    # クラス指定が完全一致でなくても通るように、より柔軟なチェックに変更
    assert 'class="slideshow-container' in response.data.decode('utf-8')
    # JSONデータに画像ファイル名が含まれていることを確認
    assert b'"test_fixture_image.png"' in response.data
    # インジケーター、全画面ボタン、速度選択要素の存在確認
    assert 'id="slide-indicator"' in response.data.decode('utf-8')
    assert 'id="toggle-fullscreen"' in response.data.decode('utf-8')
    assert 'id="speed-select"' in response.data.decode('utf-8')

    response = client.get('/slideshow/non_existent_image.jpg')
    assert response.status_code == 404

def test_slideshow_config_page(client):
    """
    スライドショー設定ページが正しく表示されるかテスト
    """
    response = client.get('/slideshow/config')
    assert response.status_code == 200
    assert 'スライドショー設定' in response.data.decode('utf-8')
    assert b'<form action="/slideshow/config/save" method="post">' in response.data
    assert '<label for="duration" class="form-label">表示時間 (ミリ秒)</label>' in response.data.decode('utf-8')
    assert '<button type="submit" class="btn btn-primary">設定を保存</button>'.encode('utf-8') in response.data

def test_save_slideshow_config(client):
    """
    スライドショー設定の保存が正しく行われるかテスト
    """
    response = client.post('/slideshow/config/save', data={'duration': '5000', 'loop_enabled': 'on'}, follow_redirects=True)
    assert response.status_code == 200
    assert '設定を保存しました。' in response.data.decode('utf-8')
    response = client.get('/slideshow/config')
    assert b'value="5000"' in response.data
    assert b'checked' in response.data # ループがチェックされていることを確認

def test_root_redirect(client):
    """
    ルートURLへのアクセスが画像一覧ページにリダイレクトされるかテスト
    """
    response = client.get('/')
    assert response.status_code == 302
    assert response.headers['Location'] == '/images'

def test_subfolder_image_access(client):
    """
    サブフォルダ内の画像にアクセスできるかテスト
    """
    img_dir = app.config['UPLOAD_FOLDER']
    subfolder_path = os.path.join(img_dir, 'sub')
    os.makedirs(subfolder_path, exist_ok=True)
    sub_image_path = os.path.join(subfolder_path, 'sub_image.png')
    with open(sub_image_path, 'w') as f:
        f.write('sub dummy')

    try:
        response = client.get('/images')
        assert response.status_code == 200
        assert b'<a href="/image/sub/sub_image.png">sub/sub_image.png</a>' in response.data

        response = client.get('/image/sub/sub_image.png')
        assert response.status_code == 200
        assert b'<img src="/static/img/sub/sub_image.png"' in response.data

        response = client.get('/slideshow/sub/sub_image.png')
        assert response.status_code == 200
        assert b'"sub/sub_image.png"' in response.data
    finally:
        # クリーンアップ
        os.remove(sub_image_path)
        os.rmdir(subfolder_path)

def test_custom_slideshow(client):
    """
    フォルダ選択（カスタム）スライドショーのテスト
    """
    img_dir = app.config['UPLOAD_FOLDER']
    
    # フォルダ構成の作成
    dir_a = os.path.join(img_dir, 'dir_a')
    sub_a = os.path.join(dir_a, 'sub_a')
    dir_b = os.path.join(img_dir, 'dir_b')
    
    os.makedirs(sub_a, exist_ok=True)
    os.makedirs(dir_b, exist_ok=True)
    
    img_a_path = os.path.join(dir_a, 'img_a.png')
    img_sub_a_path = os.path.join(sub_a, 'img_sub_a.png')
    img_b_path = os.path.join(dir_b, 'img_b.png')
    
    for path in [img_a_path, img_sub_a_path, img_b_path]:
        with open(path, 'w') as f:
            f.write('dummy')
            
    try:
        # 1. dir_a内の画像をスライドショー（再帰なし）
        response = client.get('/slideshow?dirs=dir_a&recursive=false')
        assert response.status_code == 200
        assert b'"dir_a/img_a.png"' in response.data
        assert b'"dir_a/sub_a/img_sub_a.png"' not in response.data
        
        # 2. dir_aおよびサブフォルダ内の画像（再帰あり）
        response = client.get('/slideshow?dirs=dir_a&recursive=true')
        assert response.status_code == 200
        assert b'"dir_a/img_a.png"' in response.data
        assert b'"dir_a/sub_a/img_sub_a.png"' in response.data
        
        # 3. 複数フォルダ指定
        response = client.get('/slideshow?dirs=dir_a/sub_a,dir_b&recursive=false')
        assert response.status_code == 200
        assert b'"dir_a/sub_a/img_sub_a.png"' in response.data
        assert b'"dir_b/img_b.png"' in response.data
        assert b'"dir_a/img_a.png"' not in response.data
        
        # 4. 画像が見つからない場合
        response = client.get('/slideshow?dirs=non_existent&recursive=true', follow_redirects=True)
        assert response.status_code == 200
        assert '画像ファイルが見つかりませんでした。' in response.data.decode('utf-8')

    finally:
        # クリーンアップ
        for path in [img_a_path, img_sub_a_path, img_b_path]:
            if os.path.exists(path):
                os.remove(path)
        for d in [sub_a, dir_a, dir_b]:
            if os.path.exists(d):
                os.rmdir(d)

def test_video_playback(client):
    """
    動画ファイル（mp4）の検出と表示のテスト
    """
    img_dir = app.config['UPLOAD_FOLDER']
    video_filename = 'test_fixture_video.mp4'
    video_path = os.path.join(img_dir, video_filename)
    
    with open(video_path, 'w') as f:
        f.write('dummy video data')
        
    try:
        # 1. 画像一覧に動画ファイルが含まれることを確認
        response = client.get('/images')
        assert response.status_code == 200
        assert video_filename.encode('utf-8') in response.data
        
        # 2. 個別表示画面にアクセスした際、videoタグが生成されることを確認
        response = client.get(f'/image/{video_filename}')
        assert response.status_code == 200
        assert b'<video src="/static/img/test_fixture_video.mp4"' in response.data
        assert b'<img ' not in response.data
        
        # 3. スライドショー画面にアクセスした際、JSONデータに動画ファイル名が含まれ、インライン再生用属性が存在すること
        response = client.get(f'/slideshow/{video_filename}')
        assert response.status_code == 200
        assert video_filename.encode('utf-8') in response.data
        assert b'id="slideshow-video"' in response.data
        assert b'playsinline' in response.data
        assert b'webkit-playsinline' in response.data
        assert b'muted' in response.data
        
    finally:
        if os.path.exists(video_path):
            os.remove(video_path)


def test_thumbnail_generation(client):
    """
    サムネイル生成エンドポイントの動作（画像・動画・キャッシュ・セキュリティ）をテスト
    """
    from PIL import Image
    import shutil

    img_dir = app.config['UPLOAD_FOLDER']
    thumb_dir = app.config['THUMBNAIL_FOLDER']

    real_img_name = 'test_real_image.png'
    real_img_path = os.path.join(img_dir, real_img_name)
    im = Image.new('RGB', (200, 150), color='blue')
    im.save(real_img_path, 'PNG')

    video_name = 'test_thumb_video.mp4'
    video_path = os.path.join(img_dir, video_name)
    with open(video_path, 'w') as f:
        f.write('dummy video')

    try:
        # 1. 実際の画像のサムネイル生成
        res = client.get(f'/thumbnail/{real_img_name}')
        assert res.status_code == 200
        assert res.mimetype in ['image/png', 'image/jpeg']

        # 2. キャッシュからの返却確認
        cached_file = os.path.join(thumb_dir, real_img_name)
        assert os.path.exists(cached_file)
        res_cached = client.get(f'/thumbnail/{real_img_name}')
        assert res_cached.status_code == 200

        # 3. 動画ファイルのサムネイル（SVGアイコン返却）
        res_video = client.get(f'/thumbnail/{video_name}')
        assert res_video.status_code == 200
        assert 'svg' in res_video.mimetype

        # 4. 存在しないファイル
        res_404 = client.get('/thumbnail/non_existent.png')
        assert res_404.status_code == 404

        # 5. パストラバーサル防止
        res_traversal = client.get('/thumbnail/../app.py')
        assert res_traversal.status_code == 404

    finally:
        if os.path.exists(real_img_path):
            os.remove(real_img_path)
        if os.path.exists(video_path):
            os.remove(video_path)
        if os.path.exists(thumb_dir):
            shutil.rmtree(thumb_dir)


def test_image_search_sort_pagination(client):
    """
    画像一覧での検索・ソート・ページネーションの動作をテスト
    """
    img_dir = app.config['UPLOAD_FOLDER']
    file_a = os.path.join(img_dir, 'alpha_test.png')
    file_b = os.path.join(img_dir, 'beta_test.png')
    
    with open(file_a, 'w') as f:
        f.write('a' * 100)
    with open(file_b, 'w') as f:
        f.write('b' * 500)

    try:
        # 1. 検索機能: 'alpha' で絞り込み
        res_search = client.get('/images?q=alpha')
        assert res_search.status_code == 200
        assert 'alpha_test.png' in res_search.data.decode('utf-8')
        assert 'beta_test.png' not in res_search.data.decode('utf-8')

        # 2. 検索機能: マッチしないキーワード
        res_none = client.get('/images?q=non_matching_keyword')
        assert res_none.status_code == 200
        assert '画像ファイルが見つかりませんでした。' in res_none.data.decode('utf-8')

        # 3. ソート機能: 名前降順
        res_sort_desc = client.get('/images?sort=name_desc')
        assert res_sort_desc.status_code == 200
        content = res_sort_desc.data.decode('utf-8')
        pos_b = content.find('beta_test.png')
        pos_a = content.find('alpha_test.png')
        assert pos_b != -1 and pos_a != -1
        assert pos_b < pos_a

        # 4. ページネーション: 1ページ1件
        res_p1 = client.get('/images?per_page=1&page=1')
        assert res_p1.status_code == 200
        assert 'ページ移動' in res_p1.data.decode('utf-8')

        res_p2 = client.get('/images?per_page=1&page=2')
        assert res_p2.status_code == 200

    finally:
        if os.path.exists(file_a):
            os.remove(file_a)
        if os.path.exists(file_b):
            os.remove(file_b)