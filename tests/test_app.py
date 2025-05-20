import pytest
import os
from app import app

# テストクライアントの設定
@pytest.fixture
def client():
    # テスト用の設定を適用する場合ここに記述
    app.config['TESTING'] = True
    # テスト用のUPLOAD_FOLDERを設定（一時ディレクトリなど）
    # app.config['UPLOAD_FOLDER'] = '/tmp/test_img'
    # os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # テスト用のダミー画像ファイルを作成
    test_img_dir = os.path.join(app.static_folder, 'img')
    os.makedirs(test_img_dir, exist_ok=True)
    dummy_image_path = os.path.join(test_img_dir, 'test_dummy_image.png')
    with open(dummy_image_path, 'w') as f:
        f.write('dummy content')

    with app.test_client() as client:
        yield client

    # テスト後のクリーンアップ
    os.remove(dummy_image_path)
    # os.rmdir(app.config['UPLOAD_FOLDER'])


def test_image_list_page(client):
    """
    画像ファイル一覧ページが正しく表示されるかテスト
    """
    response = client.get('/images')
    assert response.status_code == 200
    assert '画像ファイル一覧' in response.data.decode('utf-8')

    # ダミー画像ファイルへのリンクが新しい形式になっているか確認
    assert b'<a href="/image/test_dummy_image.png">test_dummy_image.png</a>' in response.data

    # 既存の画像ファイルへのリンクも新しい形式になっているか確認
    assert b'<a href="/image/code_smartphone_qrcode.png">code_smartphone_qrcode.png</a>' in response.data
    assert b'<a href="/image/kanban_closed.gif">kanban_closed.gif</a>' in response.data
    assert b'<a href="/image/seiza_fuyu_daisankaku.webp">seiza_fuyu_daisankaku.webp</a>' in response.data


def test_image_display_page(client):
    """
    画像表示ページが正しく表示されるかテスト
    """
    # 存在する画像ファイル名でテスト
    response = client.get('/image/test_dummy_image.png')
    assert response.status_code == 200
    # タイトルが正しいか確認（正規表現で<title>タグの内容を抽出）
    import re
    match = re.search(r'<title>(.*?)</title>', response.data.decode('utf-8'))
    assert match is not None
    assert match.group(1) == 'test_dummy_image.png - 画像表示 - 画像ビューワー'

    # imgタグのsrc属性が正しいか確認
    assert b'<img src="/static/img/test_dummy_image.png" alt="test_dummy_image.png">' in response.data
    # スライドショー開始リンクがあるか確認
    assert '<a href="/slideshow/test_dummy_image.png">スライドショーを開始</a>'.encode('utf-8') in response.data

    # 存在しない画像ファイル名でテスト（Flaskのデフォルトの404ページが表示されることを期待）
    response = client.get('/image/non_existent_image.jpg')
    assert response.status_code == 404

def test_slideshow_page(client):
    """
    スライドショーページが正しく表示されるかテスト
    """
    # 存在する画像ファイル名でテスト
    response = client.get('/slideshow/test_dummy_image.png')
    assert response.status_code == 200
    assert 'スライドショー' in response.data.decode('utf-8')
    # スライドショーコンテナと画像タグがあるか確認
    assert b'<div class="slideshow-container">' in response.data
    assert b'<img id="slideshow-image"' in response.data
    # JSONデータを含むスクリプトタグがあるか確認
    assert b'<script id="slideshow-data" type="application/json">' in response.data
    # JSONデータに画像ファイルリストと開始インデックスが含まれているか（部分的に）確認
    assert b'"image_files":' in response.data
    assert b'"start_index":' in response.data
    # JSONデータにスライドショー表示時間が含まれているか確認
    assert b'"slideshow_duration":' in response.data

    # 存在しない画像ファイル名でテスト
    response = client.get('/slideshow/non_existent_image.jpg')
    assert response.status_code == 404

def test_slideshow_config_page(client):
    """
    スライドショー設定ページが正しく表示されるかテスト
    """
    response = client.get('/slideshow/config')
    assert response.status_code == 200
    assert 'スライドショー設定' in response.data.decode('utf-8')
    # フォームと入力フィールド、保存ボタンがあるか確認
    assert b'<form action="/slideshow/config/save" method="post">' in response.data
    assert '<label for="duration">表示時間 (ミリ秒):</label>' in response.data.decode('utf-8')
    assert b'<input type="number" id="duration" name="duration"' in response.data
    assert '<button type="submit">保存</button>'.encode('utf-8') in response.data

def test_save_slideshow_config(client):
    """
    スライドショー設定の保存が正しく行われるかテスト
    """
    # POSTリクエストで設定を保存
    response = client.post('/slideshow/config/save', data={'duration': 5000}, follow_redirects=True)
    assert response.status_code == 200 # リダイレクト後のページ
    assert 'スライドショー設定' in response.data.decode('utf-8')
    assert 'スライドショー表示時間を保存しました。' in response.data.decode('utf-8')

    # 設定が反映されているか確認（設定ページを再度取得して入力フィールドの値を確認）
    response = client.get('/slideshow/config')
    assert b'value="5000"' in response.data

    # 無効な入力値のテスト（数値以外）
    response = client.post('/slideshow/config/save', data={'duration': 'abc'}, follow_redirects=True)
    assert response.status_code == 200
    assert '無効な数値が入力されました。' in response.data.decode('utf-8')

    # 無効な入力値のテスト（最小値未満）
    response = client.post('/slideshow/config/save', data={'duration': 100}, follow_redirects=True)
    assert response.status_code == 200
    assert '表示時間は500ミリ秒以上にしてください。' in response.data.decode('utf-8')