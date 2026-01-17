from models import Room, Bed, RoomState, BedState, StateChangeLog, Status, User, Area, SystemJobState
from peewee import JOIN, prefetch, fn, Case
import config
import datetime

def get_board_data(area_id):
    # エリア内のアクティブな部屋を取得
    rooms = Room.select().where(Room.area == area_id, Room.is_active == True).order_by(Room.sort_order)
    
    # アクティブなベッドと状態をプリフェッチ
    # ※is_available=Falseのベッドもボード上には表示するため、is_activeのみで絞り込む
    beds = Bed.select().where(Bed.is_active == True).order_by(Bed.sort_order)
    # Statusも明示的に含めてプリフェッチ
    bed_states = BedState.select()
    room_states = RoomState.select()
    
    # prefetchを使用してRoom -> Bed -> BedState -> Status と Room -> RoomState -> Status を一括取得
    rooms_with_data = prefetch(rooms, room_states, beds, bed_states, Status.select())
    
    rooms_data = []
    for room in rooms_with_data:
        # ベッドがある場合
        bed_list = []
        for bed in room.beds:
            state = None
            if hasattr(bed, 'state'):
                # prefetchにより bed.state はリストになっている可能性がある
                state = bed.state[0] if bed.state else None
            
            bed_list.append({
                'obj': bed,
                'state': state
            })
            
        # 部屋の状態（ベッドがない場合のみ使用される想定）
        room_state = None
        if hasattr(room, 'state'):
            room_state = room.state[0] if room.state else None
            
        rooms_data.append({
            'room': room,
            'beds': bed_list,
            'room_state': room_state
        })
    return rooms_data

def update_room_state(room_id, status_id, user):
    room = Room.get_by_id(room_id)
    status = Status.get_by_id(status_id)
    
    state, created = RoomState.get_or_create(room=room, defaults={'status': status})
    old_status = None if created else state.status
    
    state.status = status
    state.updated_by = user
    state.updated_at = datetime.datetime.now() # 明示的に更新
    state.save()
    
    # 履歴保存
    StateChangeLog.create(
        target_type='room',
        room=room,
        area=room.area,
        from_status=old_status,
        to_status=status,
        changed_by=user
    )

def update_bed_state(bed_id, status_id, user):
    bed = Bed.get_by_id(bed_id)
    status = Status.get_by_id(status_id)
    
    state, created = BedState.get_or_create(bed=bed, defaults={'status': status})
    old_status = None if created else state.status
    
    state.status = status
    state.updated_by = user
    state.updated_at = datetime.datetime.now() # 明示的に更新
    state.save()
    
    # 履歴保存
    StateChangeLog.create(
        target_type='bed',
        bed=bed,
        area=bed.room.area,
        from_status=old_status,
        to_status=status,
        changed_by=user
    )

def get_bed_counts(area_id=None):
    """
    エリアごとのベッド集計を取得する
    """
    # 対象エリアの取得
    if area_id:
        areas = Area.select().where(Area.id == area_id, Area.is_active == True)
    else:
        areas = Area.select().where(Area.is_active == True).order_by(Area.sort_order)
    
    # 全ての有効なステータスを取得（辞書化）
    occupied_status_ids = [s.id for s in Status.select().where(Status.key << config.OCCUPIED_STATUS_KEYS)]
    
    # VACANT_STATUS_KEYS に含まれるもの、または status が設定されていないものを「空き」とみなす
    # ただし、現状のロジックでは BedState が必ず存在することを想定しているか、
    # BedState がない場合は「未設定」として扱われ、occupied にはカウントされない
    
    results = []
    for area in areas:
        # このエリアのアクティブな全ベッドを取得 (is_active=True)
        # かつ is_available=True のものがカウント対象
        beds_query = Bed.select().join(Room).where(Room.area == area, Bed.is_active == True)
        
        total_available = beds_query.where(Bed.is_available == True).count()
        unavailable = beds_query.where(Bed.is_available == False).count()
        
        # BedState と JOIN して現在のステータスを判定
        occupied_count = (BedState.select()
                          .join(Bed).join(Room)
                          .where(Room.area == area, 
                                 Bed.is_active == True, 
                                 Bed.is_available == True,
                                 BedState.status << occupied_status_ids)
                          .count())
        
        # 空き数は「総運用病床数 - 利用中数」で計算（仕様の通り）
        results.append({
            'area': area,
            'total_available_beds': total_available,
            'unavailable_beds': unavailable,
            'occupied_beds': occupied_count,
            'vacant_beds': total_available - occupied_count,
            'updated_at': datetime.datetime.now() # 簡易的に現在時刻
        })
        
    return results

def maybe_run_auto_reset(now=None):
    if not config.AUTO_RESET_ENABLED:
        return

    if now is None:
        now = datetime.datetime.now()
    
    # リセット予定時刻を取得 (HH:MM)
    reset_at_hour, reset_at_minute = map(int, config.AUTO_RESET_AT.split(':'))
    reset_time_today = now.replace(hour=reset_at_hour, minute=reset_at_minute, second=0, microsecond=0)
    
    # 現在時刻がリセット予定時刻を過ぎているか確認
    if now < reset_time_today:
        return
        
    # DBから最終実行状況を確認
    job_state, created = SystemJobState.get_or_create(job_key='auto_reset')
    
    # 今日すでに実行済みならスキップ
    if job_state.last_run_date == now.date():
        return
        
    # 実行
    run_auto_reset(now)
    
    # 実行済み記録
    job_state.last_run_at = now
    job_state.last_run_date = now.date()
    job_state.save()

def run_auto_reset(now):
    # Status.key から Status オブジェクトへのマッピングを作成
    status_map = {s.key: s for s in Status.select()}
    
    rules = []
    for from_key, to_key in config.AUTO_RESET_RULES.items():
        if from_key in status_map and to_key in status_map:
            rules.append((status_map[from_key], status_map[to_key]))
            
    if not rules:
        return
        
    # 対象エリアのフィルタリング
    area_ids = []
    if config.AUTO_RESET_SCOPE == "area":
        area_ids = config.AUTO_RESET_AREAS
        
    total_updated = 0
    
    # RoomStateの一括更新
    for from_status, to_status in rules:
        query = RoomState.update(status=to_status, updated_at=now).where(RoomState.status == from_status)
        if area_ids:
            query = query.where(RoomState.room << Room.select(Room.id).where(Room.area << area_ids))
        
        count = query.execute()
        total_updated += count
        
        if count > 0 and config.AUTO_RESET_LOG_MODE == "per_item":
            # 個別ログ
            rooms_to_log = Room.select().join(RoomState).where(RoomState.status == to_status) # 更新後なのでto_status
            if area_ids:
                rooms_to_log = rooms_to_log.where(Room.area << area_ids)
                
            # 注意: ここでは「今更新されたもの」を厳密に特定するのが難しい（一括更新後なので）
            # 本来は更新前に取得するか、1つずつ更新する必要があるが、パフォーマンス優先で「サマリーログ」を推奨。
            # v1.4ではサマリーをデフォルトとする。
            pass

    # BedStateの一括更新
    for from_status, to_status in rules:
        query = BedState.update(status=to_status, updated_at=now).where(BedState.status == from_status)
        if area_ids:
            query = query.where(BedState.bed << Bed.select(Bed.id).join(Room).where(Room.area << area_ids))
            
        count = query.execute()
        total_updated += count

    # 履歴保存 (Summary)
    if total_updated > 0:
        StateChangeLog.create(
            target_type='system',
            to_status=None, # systemの場合はNoneを許容するか、Metaに書く
            meta=f"auto_reset: {total_updated} items updated",
            note=f"自動リセット実行: {total_updated}件更新されました。",
            changed_at=now
        )
