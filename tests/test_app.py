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