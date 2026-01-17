from bottle import get, post, request, redirect, jinja2_template as template
from models import User, Area, Room, Bed, Status, StateChangeLog
import auth
import datetime
import config

@get('/admin')
@auth.role_required('admin')
def admin_index():
    return template('admin/index.html', user=auth.get_current_user())

# --- Area Management ---
@get('/admin/areas')
@auth.role_required('admin')
def admin_areas():
    areas = Area.select().order_by(Area.sort_order)
    return template('admin/areas.html', areas=areas, user=auth.get_current_user())

@get('/admin/areas/new')
@auth.role_required('admin')
def admin_areas_new():
    return template('admin/area_edit.html', area=None, user=auth.get_current_user())

@post('/admin/areas/new')
@auth.role_required('admin')
def admin_areas_create():
    Area.create(
        name=request.forms.decode().get('name'),
        sort_order=int(request.forms.decode().get('sort_order', 0))
    )
    return redirect('/admin/areas')

@get('/admin/areas/<id:int>/edit')
@auth.role_required('admin')
def admin_areas_edit(id):
    area = Area.get_by_id(id)
    return template('admin/area_edit.html', area=area, user=auth.get_current_user())

@post('/admin/areas/<id:int>/edit')
@auth.role_required('admin')
def admin_areas_update(id):
    area = Area.get_by_id(id)
    area.name = request.forms.decode().get('name')
    area.sort_order = int(request.forms.decode().get('sort_order', 0))
    area.save()
    return redirect('/admin/areas')

@post('/admin/areas/<id:int>/toggle_active')
@auth.role_required('admin')
def admin_areas_toggle(id):
    area = Area.get_by_id(id)
    area.is_active = not area.is_active
    area.save()
    return redirect('/admin/areas')

# --- Room Management ---
@get('/admin/rooms')
@auth.role_required('admin')
def admin_rooms():
    rooms = Room.select().order_by(Room.area, Room.sort_order)
    return template('admin/rooms.html', rooms=rooms, user=auth.get_current_user())

@get('/admin/rooms/new')
@auth.role_required('admin')
def admin_rooms_new():
    areas = Area.select().where(Area.is_active == True)
    return template('admin/room_edit.html', room=None, areas=areas, user=auth.get_current_user())

@post('/admin/rooms/new')
@auth.role_required('admin')
def admin_rooms_create():
    Room.create(
        area=request.forms.decode().get('area_id'),
        code=request.forms.decode().get('code'),
        name=request.forms.decode().get('name'),
        sort_order=int(request.forms.decode().get('sort_order', 0))
    )
    return redirect('/admin/rooms')

@get('/admin/rooms/<id:int>/edit')
@auth.role_required('admin')
def admin_rooms_edit(id):
    room = Room.get_by_id(id)
    areas = Area.select().where(Area.is_active == True)
    return template('admin/room_edit.html', room=room, areas=areas, user=auth.get_current_user())

@post('/admin/rooms/<id:int>/edit')
@auth.role_required('admin')
def admin_rooms_update(id):
    room = Room.get_by_id(id)
    room.area = request.forms.decode().get('area_id')
    room.code = request.forms.decode().get('code')
    room.name = request.forms.decode().get('name')
    room.sort_order = int(request.forms.decode().get('sort_order', 0))
    room.save()
    return redirect('/admin/rooms')

@post('/admin/rooms/<id:int>/toggle_active')
@auth.role_required('admin')
def admin_rooms_toggle(id):
    room = Room.get_by_id(id)
    room.is_active = not room.is_active
    room.save()
    return redirect('/admin/rooms')

# --- Bed Management ---
@get('/admin/beds')
@auth.role_required('admin')
def admin_beds():
    area_id = request.query.get('area_id')
    room_id = request.query.get('room_id')

    query = Bed.select().join(Room)
    
    if room_id:
        query = query.where(Bed.room == room_id)
    elif area_id:
        query = query.where(Room.area == area_id)

    beds = query.order_by(Bed.room, Bed.sort_order)
    
    areas = Area.select().order_by(Area.sort_order)
    rooms = Room.select().order_by(Room.sort_order)
    if area_id:
        rooms = rooms.where(Room.area == area_id)
        
    return template('admin/beds.html', 
                    beds=beds, 
                    areas=areas, 
                    rooms=rooms,
                    selected_area_id=int(area_id) if area_id else None,
                    selected_room_id=int(room_id) if room_id else None,
                    user=auth.get_current_user())

@get('/admin/beds/new')
@auth.role_required('admin')
def admin_beds_new():
    rooms = Room.select().where(Room.is_active == True)
    return template('admin/bed_edit.html', bed=None, rooms=rooms, user=auth.get_current_user())

@post('/admin/beds/new')
@auth.role_required('admin')
def admin_beds_create():
    Bed.create(
        room=request.forms.decode().get('room_id'),
        code=request.forms.decode().get('code'),
        name=request.forms.decode().get('name'),
        sort_order=int(request.forms.decode().get('sort_order', 0)),
        is_available=request.forms.decode().get('is_available') == 'on'
    )
    return redirect('/admin/beds')

@get('/admin/beds/<id:int>/edit')
@auth.role_required('admin')
def admin_beds_edit(id):
    bed = Bed.get_by_id(id)
    rooms = Room.select().where(Room.is_active == True)
    return template('admin/bed_edit.html', bed=bed, rooms=rooms, user=auth.get_current_user())

@post('/admin/beds/<id:int>/edit')
@auth.role_required('admin')
def admin_beds_update(id):
    bed = Bed.get_by_id(id)
    bed.room = request.forms.decode().get('room_id')
    bed.code = request.forms.decode().get('code')
    bed.name = request.forms.decode().get('name')
    bed.sort_order = int(request.forms.decode().get('sort_order', 0))
    bed.is_available = request.forms.decode().get('is_available') == 'on'
    bed.save()
    return redirect('/admin/beds')

@post('/admin/beds/<id:int>/toggle_active')
@auth.role_required('admin')
def admin_beds_toggle(id):
    bed = Bed.get_by_id(id)
    bed.is_active = not bed.is_active
    bed.save()
    return redirect('/admin/beds')

# --- Status Management ---
@get('/admin/statuses')
@auth.role_required('admin')
def admin_statuses():
    statuses = Status.select().order_by(Status.sort_order)
    return template('admin/statuses.html', statuses=statuses, user=auth.get_current_user())

@get('/admin/statuses/new')
@auth.role_required('admin')
def admin_statuses_new():
    return template('admin/status_edit.html', status_obj=None, user=auth.get_current_user())

@post('/admin/statuses/new')
@auth.role_required('admin')
def admin_statuses_create():
    Status.create(
        key=request.forms.decode().get('key'),
        label=request.forms.decode().get('label'),
        color_class=request.forms.decode().get('color_class'),
        icon_class=request.forms.decode().get('icon_class'),
        sort_order=int(request.forms.decode().get('sort_order', 0)),
        applies_to_room=request.forms.decode().get('applies_to_room') == 'on',
        applies_to_bed=request.forms.decode().get('applies_to_bed') == 'on'
    )
    return redirect('/admin/statuses')

@get('/admin/statuses/<id:int>/edit')
@auth.role_required('admin')
def admin_statuses_edit(id):
    status_obj = Status.get_by_id(id)
    return template('admin/status_edit.html', status_obj=status_obj, user=auth.get_current_user())

@post('/admin/statuses/<id:int>/edit')
@auth.role_required('admin')
def admin_statuses_update(id):
    status_obj = Status.get_by_id(id)
    status_obj.key = request.forms.decode().get('key')
    status_obj.label = request.forms.decode().get('label')
    status_obj.color_class = request.forms.decode().get('color_class')
    status_obj.icon_class = request.forms.decode().get('icon_class')
    status_obj.sort_order = int(request.forms.decode().get('sort_order', 0))
    status_obj.applies_to_room = request.forms.decode().get('applies_to_room') == 'on'
    status_obj.applies_to_bed = request.forms.decode().get('applies_to_bed') == 'on'
    status_obj.save()
    return redirect('/admin/statuses')

# --- User Management ---
@get('/admin/users')
@auth.role_required('admin')
def admin_users():
    users = User.select()
    return template('admin/users.html', users=users, user=auth.get_current_user())

@get('/admin/users/new')
@auth.role_required('admin')
def admin_users_new():
    return template('admin/user_edit.html', edit_user=None, user=auth.get_current_user())

@post('/admin/users/new')
@auth.role_required('admin')
def admin_users_create():
    username = request.forms.decode().get('username')
    password = request.forms.decode().get('password')
    role = request.forms.decode().get('role')
    
    password_hash, salt = auth.hash_password(password)
    User.create(
        username=username,
        password_hash=password_hash,
        salt=salt,
        role=role
    )
    return redirect('/admin/users')

@get('/admin/users/<id:int>/edit')
@auth.role_required('admin')
def admin_users_edit(id):
    edit_user = User.get_by_id(id)
    return template('admin/user_edit.html', edit_user=edit_user, user=auth.get_current_user())

@post('/admin/users/<id:int>/edit')
@auth.role_required('admin')
def admin_users_update(id):
    edit_user = User.get_by_id(id)
    edit_user.username = request.forms.decode().get('username')
    edit_user.role = request.forms.decode().get('role')
    
    password = request.forms.decode().get('password')
    if password:
        password_hash, salt = auth.hash_password(password)
        edit_user.password_hash = password_hash
        edit_user.salt = salt
        
    edit_user.save()
    return redirect('/admin/users')

@post('/admin/users/<id:int>/toggle_active')
@auth.role_required('admin')
def admin_users_toggle(id):
    u = User.get_by_id(id)
    # 自分自身は無効化できない
    if u.id != auth.get_current_user().id:
        u.is_active = not u.is_active
        u.save()
    return redirect('/admin/users')

# --- Log Management ---
@get('/admin/logs')
@auth.role_required('admin')
def admin_logs():
    try:
        query = StateChangeLog.select().order_by(StateChangeLog.changed_at.desc())
        
        # フィルタ
        area_id = request.query.get('area_id')
        if area_id:
            query = query.where(StateChangeLog.area == area_id)
            
        target_type = request.query.get('target_type')
        if target_type:
            query = query.where(StateChangeLog.target_type == target_type)
            
        user_id = request.query.get('user_id')
        if user_id:
            query = query.where(StateChangeLog.changed_by == user_id)
        
        # ページネーション（簡易的に直近100件などでも良いが、一旦全て表示 or 制限なし）
        logs = list(query.limit(200)) # パフォーマンスのため一旦200件
        
        areas = list(Area.select())
        users = list(User.select())
        
        return template('admin/logs.html', 
                        logs=logs, 
                        areas=areas, 
                        users=users,
                        selected_area=area_id,
                        selected_target=target_type,
                        selected_user=user_id,
                        user=auth.get_current_user(),
                        config=config)
    except Exception:
        raise

@post('/admin/logs/purge')
@auth.role_required('admin')
def admin_logs_purge():
    days = config.LOG_RETENTION_DAYS
    if days > 0:
        threshold = datetime.datetime.now() - datetime.timedelta(days=days)
        StateChangeLog.delete().where(StateChangeLog.changed_at < threshold).execute()
    return redirect('/admin/logs')
