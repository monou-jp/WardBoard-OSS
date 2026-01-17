import datetime
import random
from models import db, User, Area, Room, Bed, Status, RoomState, BedState, init_db
import config

def seed():
    print("Initializing database...")
    init_db()
    
    # db.connect() は init_db 内で行われているが、close されているので再度開く
    db.connect(reuse_if_open=True)
    
    # すでにデータがあるか確認
    if Area.select().count() > 0:
        confirm = input("Database already contains data. Do you want to clear it first? (y/N): ")
        if confirm.lower() == 'y':
            print("Clearing existing data...")
            # 外部キー制約を考慮して削除
            StateChangeLog.delete().execute()
            BedState.delete().execute()
            RoomState.delete().execute()
            Bed.delete().execute()
            Room.delete().execute()
            Area.delete().execute()
            # Status と User は init_db で入るので消さないか、消したなら再度 init_db する必要がある
        else:
            print("Appending to existing data...")

    print("Seeding dummy data...")

    # ステータスの取得
    statuses = list(Status.select())
    if not statuses:
        print("No statuses found. Please ensure init_db() worked correctly.")
        return
    
    # ユーザーの取得（更新者として使用）
    admin_user = User.get(User.username == config.DEFAULT_ADMIN_USER)

    # ダミーデータの定義
    area_names = ["一般病棟", "ICU", "産科病棟"]
    
    for i, area_name in enumerate(area_names):
        area = Area.create(name=area_name, sort_order=i+1)
        print(f"Created Area: {area_name}")
        
        # 部屋の作成 (1病棟あたり4部屋程度)
        for r in range(1, 5):
            room_code = f"{100 + i*10 + r}"
            room_name = f"{room_code}号室"
            room = Room.create(
                area=area,
                code=room_code,
                name=room_name,
                sort_order=r
            )
            
            # 部屋の初期状態
            RoomState.create(
                room=room,
                status=random.choice(statuses),
                updated_by=admin_user,
                note="初期データ",
                updated_at=None # 初期状態は「---」にするため
            )
            
            # ベッドの作成 (1部屋あたり2-4ベッド)
            num_beds = random.randint(2, 4)
            for b in range(1, num_beds + 1):
                bed_code = f"{room_code}-{b}"
                bed_name = f"{b}番ベッド"
                bed = Bed.create(
                    room=room,
                    code=bed_code,
                    name=bed_name,
                    sort_order=b
                )
                
                # ベッドの初期状態
                BedState.create(
                    bed=bed,
                    status=random.choice(statuses),
                    updated_by=admin_user,
                    note="初期データ",
                    updated_at=None # 初期状態は「---」にするため
                )
    
    print("Done! Dummy data has been successfully inserted.")
    db.close()

if __name__ == "__main__":
    from models import StateChangeLog # 削除時に必要
    seed()
