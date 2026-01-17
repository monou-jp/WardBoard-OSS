import pytest
from models import User

def test_install_and_login(test_app):
    # 初期状態（init_db実行後）では既に管理者が存在するため、/install は /login へリダイレクトされる
    res = test_app.get("/install")
    assert res.status_code == 302
    assert "/login" in res.headers['Location']
    
    # 既存の管理者を削除して /install をテスト可能にする
    User.delete().where(User.role == 'admin').execute()
    
    res = test_app.get("/install")
    assert res.status_code == 200
    assert "初期セットアップ" in res

    # 管理者作成
    form = res.forms[0]
    form['username'] = "admin"
    form['password'] = "password123"
    form['confirm'] = "password123"
    # redirect 302 を follow する
    res = form.submit().follow()

    assert "/login" in res.request.url
    assert User.select().where(User.username == "admin").exists()

    # ログイン
    form = res.forms[0]
    form['username'] = "admin"
    form['password'] = "password123"
    res = form.submit().follow()
    
    # ログイン後はトップページ（エリアがないのでメッセージまたは管理画面へ）
    if res.status_code == 302:
        res = res.follow()
    assert res.status_code == 200

def test_login_failure(test_app):
    # setup_db で作成されたデフォルト管理者を使用
    res = test_app.get("/login")
    form = res.forms[0]
    form['username'] = "admin"
    form['password'] = "wrongpass"
    res = form.submit()
    
    assert "IDまたはパスワードが正しくありません" in res

def test_logout(test_app, auth_helper):
    # setup_db で作成されたデフォルト管理者を使用
    auth_helper.login("admin", "admin")
    res = test_app.post("/logout").follow()
    assert "/login" in res.request.url

def test_auth_required(test_app):
    # 未ログインでのアクセス制限
    res = test_app.get("/", status=302)
    assert "/login" in res.headers['Location']
    
    res = test_app.get("/admin", status=302)
    assert "/login" in res.headers['Location']

def test_role_permission(test_app, viewer_user, operator_user, auth_helper):
    # viewer は管理画面にアクセスできない
    auth_helper.login("viewer", "viewerpass")
    res = test_app.get("/admin")
    assert "Permission Denied" in res
    
    # 一旦ログアウト
    test_app.post("/logout")
    
    # operator も管理画面（インデックス以外）にはアクセスできないはず（実装を確認）
    # views_admin.py の各関数は @auth.role_required('admin') がついている
    auth_helper.login("operator", "operatorpass")
    res = test_app.get("/admin")
    assert "Permission Denied" in res

def test_session_tampering(test_app):
    # ログインしてクッキーを取得
    res = test_app.get("/login")
    form = res.forms[0]
    form['username'] = "admin"
    form['password'] = "admin"
    res = form.submit()
    
    # ログインできていることを確認
    res = test_app.get("/admin")
    assert res.status_code == 200
    
    # クッキーを削除
    test_app.reset() # クッキーとセッションを完全にリセット
    
    # アクセスすると未ログイン扱い（リダイレクトされる）
    res = test_app.get("/admin", status=302)
    assert "/login" in res.headers['Location']

def test_inactive_user_cannot_login(test_app):
    # setup_db で作成されたデフォルト管理者を取得して無効化
    admin = User.get(User.username == "admin")
    admin.is_active = False
    admin.save()
    
    res = test_app.get("/login")
    form = res.forms[0]
    form['username'] = "admin"
    form['password'] = "admin"
    res = form.submit()
    
    assert "IDまたはパスワードが正しくありません" in res
