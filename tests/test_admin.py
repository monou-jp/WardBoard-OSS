import pytest
from models import Area, Room, Bed, Status, User

def test_admin_area_crud(test_app, admin_user, auth_helper):
    # admin_user が admin/admin または admin/adminpass のいずれかであることを考慮
    # ログインを試行
    try:
        auth_helper.login("admin", "admin")
    except:
        auth_helper.login("admin", "adminpass")
    
    # 一覧
    res = test_app.get("/admin/areas")
    assert res.status_code == 200
    
    # 新規作成 (エンコーディング問題を避けるため英数字を使用)
    res = test_app.post("/admin/areas/new", {
        "name": "NewArea",
        "sort_order": "10"
    })
    assert res.status_code == 302
    assert Area.select().where(Area.name == "NewArea").exists()
    area = Area.get(Area.name == "NewArea")
    
    # 編集
    res = test_app.post(f"/admin/areas/{area.id}/edit", {
        "name": "UpdatedArea",
        "sort_order": "10"
    }).follow()
    assert "UpdatedArea" in res
    assert Area.get_by_id(area.id).name == "UpdatedArea"
    
    # 無効化
    res = test_app.post(f"/admin/areas/{area.id}/toggle_active").follow()
    assert Area.get_by_id(area.id).is_active == False

def test_admin_room_crud(test_app, admin_user, auth_helper):
    try:
        auth_helper.login("admin", "admin")
    except:
        auth_helper.login("admin", "adminpass")
    area = Area.create(name="Area1")
    
    # 新規作成
    res = test_app.post("/admin/rooms/new", {
        "area_id": str(area.id),
        "code": "R101",
        "name": "Room101",
        "sort_order": "0"
    }).follow()
    
    assert "R101" in res
    assert Room.select().where(Room.code == "R101").exists()

def test_admin_user_crud(test_app, admin_user, auth_helper):
    try:
        auth_helper.login("admin", "admin")
    except:
        auth_helper.login("admin", "adminpass")
    
    # 新規作成
    res = test_app.post("/admin/users/new", {
        "username": "newuser",
        "password": "newpass",
        "role": "operator"
    }).follow()
    
    assert "newuser" in res
    assert User.select().where(User.username == "newuser").exists()
    user = User.get(User.username == "newuser")
    assert user.role == "operator"

def test_admin_logs(test_app, admin_user, auth_helper):
    try:
        auth_helper.login("admin", "admin")
    except:
        auth_helper.login("admin", "adminpass")
    res = test_app.get("/admin/logs")
    assert res.status_code == 200

def test_admin_status_crud(test_app, admin_user, auth_helper):
    try:
        auth_helper.login("admin", "admin")
    except:
        auth_helper.login("admin", "adminpass")
    
    # 新規作成
    res = test_app.post("/admin/statuses/new", {
        "key": "custom_status",
        "label": "CustomLabel",
        "color_class": "bg-primary",
        "icon_class": "bi-star",
        "sort_order": "0",
        "applies_to_room": "on",
        "applies_to_bed": "on"
    }).follow()
    
    assert "custom_status" in res
    assert Status.select().where(Status.key == "custom_status").exists()

def test_admin_beds_filtering(test_app, admin_user, auth_helper):
    try:
        auth_helper.login("admin", "admin")
    except:
        auth_helper.login("admin", "adminpass")
    
    # データの準備
    area1 = Area.create(name="Area1", sort_order=1)
    area2 = Area.create(name="Area2", sort_order=2)
    
    room1 = Room.create(area=area1, code="R1", name="Room1", sort_order=1)
    room2 = Room.create(area=area2, code="R2", name="Room2", sort_order=2)
    
    bed1 = Bed.create(room=room1, code="B1", name="Bed1", sort_order=1)
    bed2 = Bed.create(room=room2, code="B2", name="Bed2", sort_order=2)
    
    # フィルタなし
    res = test_app.get("/admin/beds")
    assert "Bed1" in res.text
    assert "Bed2" in res.text
    
    # エリアでフィルタ
    res = test_app.get(f"/admin/beds?area_id={area1.id}")
    assert "Bed1" in res.text
    assert "Bed2" not in res.text
    
    # 部屋でフィルタ
    res = test_app.get(f"/admin/beds?room_id={room2.id}")
    assert "Bed1" not in res.text
    assert "Bed2" in res.text
    
    # 両方（矛盾しない場合）
    res = test_app.get(f"/admin/beds?area_id={area1.id}&room_id={room1.id}")
    assert "Bed1" in res.text
    assert "Bed2" not in res.text
