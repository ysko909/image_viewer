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
    assert '画像表示' in response.data.decode('utf-8')
    # imgタグのsrc属性が正しいか確認
    assert b'<img src="/static/img/test_dummy_image.png" alt="test_dummy_image.png">' in response.data

    # 存在しない画像ファイル名でテスト（Flaskのデフォルトの404ページが表示されることを期待）
    response = client.get('/image/non_existent_image.jpg')
    assert response.status_code == 404