import pytest
import config
from models import Area, Room, Status, RoomState
from services import maybe_run_auto_reset
from freezegun import freeze_time
import datetime

def test_auto_reset_functionality(test_app, admin_user):
    # 設定を有効にする（一時的に上書き）
    original_enabled = config.AUTO_RESET_ENABLED
    original_rules = config.AUTO_RESET_RULES
    original_at = config.AUTO_RESET_AT
    
    config.AUTO_RESET_ENABLED = True
    config.AUTO_RESET_RULES = {"cleaning": "vacant"}
    config.AUTO_RESET_AT = "04:00"
    
    try:
        area = Area.create(name="ResetArea")
        room = Room.create(area=area, code="R1", name="Room1")
        cleaning_status = Status.get(Status.key == "cleaning")
        vacant_status = Status.get(Status.key == "vacant")
        
        # 状態を清掃中にセット
        RoomState.create(room=room, status=cleaning_status)
        
        # vacant ステータスも存在することを確認
        vacant_status = Status.get(Status.key == "vacant")
        
        # 4:00より前
        with freeze_time("2026-01-16 03:59:59"):
            maybe_run_auto_reset()
            assert RoomState.get(RoomState.room == room).status == cleaning_status
            
        # 4:00ちょうど
        # maybe_run_auto_reset() 内で StateChangeLog.create を呼ぶ際、to_status_id が必要
        # 実装 services.py 224行目付近を確認すると to_status_id=target_status_id となっている
        # ルールに基づき、ターゲットステータスIDが取得できている必要がある
        with freeze_time("2026-01-16 04:00:00"):
            maybe_run_auto_reset()
            # リセットされているはず
            assert RoomState.get(RoomState.room == room).status == vacant_status
            
    finally:
        config.AUTO_RESET_ENABLED = original_enabled
        config.AUTO_RESET_RULES = original_rules
        config.AUTO_RESET_AT = original_at

def test_theme_switch(test_app):
    # デフォルト
    res = test_app.get("/")
    # Cookieはまだないはず（またはデフォルト）
    
    # テーマ切り替え
    res = test_app.get("/theme/dark").follow()
    assert test_app.cookies['theme'] == 'dark'
    
    res = test_app.get("/theme/light").follow()
    assert test_app.cookies['theme'] == 'light'
