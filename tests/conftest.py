import pytest
import os
import tempfile
from webtest import TestApp
from index import create_app
import models
import auth
import config

@pytest.fixture(scope="session")
def db_path():
    fd, path = tempfile.mkstemp()
    os.close(fd)
    
    # セッション開始時に一度だけ初期化
    models.db.init(path)
    models.db.connect()
    models.db.create_tables([
        models.User, models.Area, models.Room, models.Bed, 
        models.Status, models.RoomState, models.BedState, 
        models.StateChangeLog, models.SystemJobState
    ])
    models.db.close()
    
    yield path
    
    if os.path.exists(path):
        try:
            os.unlink(path)
        except PermissionError:
            pass

@pytest.fixture(scope="session")
def app(db_path):
    # アプリ作成時にDBパスを固定
    app = create_app(db_path)
    return app

@pytest.fixture
def test_app(app):
    return TestApp(app)

@pytest.fixture(autouse=True)
def setup_db(db_path):
    # テストごとにデータをクリア
    # models.db.init(db_path) # 不要：sessionスコープで実施済み
    with models.db:
        # 外部キー制約を考慮した削除順
        models.StateChangeLog.delete().execute()
        models.BedState.delete().execute()
        models.RoomState.delete().execute()
        models.Bed.delete().execute()
        models.Room.delete().execute()
        models.Area.delete().execute()
        models.User.delete().execute()
        models.Status.delete().execute()
        models.SystemJobState.delete().execute()

        for s in config.INITIAL_STATUSES:
            models.Status.create(**s)
            
        # init_db の挙動を再現するため、デフォルト管理者を再作成する
        # (models.init_db は session スコープで呼ばれるが、テストごとに User はクリアされるため)
        from auth import hash_password
        password_hash, salt = hash_password(config.DEFAULT_ADMIN_PASSWORD)
        models.User.create(
            username=config.DEFAULT_ADMIN_USER,
            password_hash=password_hash,
            salt=salt,
            role='admin'
        )
    yield

@pytest.fixture
def admin_user():
    user = models.User.get_or_none(models.User.username == "admin")
    if user:
        return user
    password_hash, salt = auth.hash_password("adminpass")
    return models.User.create(
        username="admin",
        password_hash=password_hash,
        salt=salt,
        role="admin"
    )

@pytest.fixture
def operator_user():
    password_hash, salt = auth.hash_password("operatorpass")
    return models.User.create(
        username="operator",
        password_hash=password_hash,
        salt=salt,
        role="operator"
    )

@pytest.fixture
def viewer_user():
    password_hash, salt = auth.hash_password("viewerpass")
    return models.User.create(
        username="viewer",
        password_hash=password_hash,
        salt=salt,
        role="viewer"
    )

class AuthHelper:
    def __init__(self, test_app):
        self.test_app = test_app

    def login(self, username, password):
        res = self.test_app.get("/login")
        # フォームからログイン
        form = res.forms[0]
        form['username'] = username
        form['password'] = password
        return form.submit()

    def get_csrf_token(self, url="/"):
        res = self.test_app.get(url)
        # ページ内の hidden input から CSRF トークンを取得
        # または、Bottleのセッションから直接取得するのは難しい（署名されているため）
        # なので、HTML内の input[name="csrf_token"] を探す
        try:
            token_input = res.html.find("input", {"name": "csrf_token"})
            if token_input:
                return token_input["value"]
            return None
        except (TypeError, KeyError, AttributeError):
            return None

    def get_form(self, url, index=0):
        res = self.test_app.get(url)
        # WebTestのフォーム解析がうまくいかない場合があるため、明示的にactionを確認
        form = res.forms[index]
        return form

@pytest.fixture
def auth_helper(test_app):
    return AuthHelper(test_app)
