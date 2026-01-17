from bottle import get, post, request, redirect, jinja2_template as template, response
from models import User, Area, Status, Room, Bed
import auth
import services
import config
import datetime

# --- v1.4 新機能用ヘルパー ---
def get_current_theme():
    if not config.ALLOW_THEME_SWITCH:
        return config.DEFAULT_THEME
    return request.get_cookie('theme', config.DEFAULT_THEME)

# --- フック ---
def before_request():
    services.maybe_run_auto_reset()

@get('/login')
def login_page():
    if auth.get_current_user():
        return redirect('/')
    return template('login.html', error=None)

@post('/login')
def login_handler():
    username = request.forms.decode().get('username')
    password = request.forms.decode().get('password')
    
    user = User.get_or_none(User.username == username, User.is_active == True)
    if user and auth.verify_password(password, user.salt, user.password_hash):
        auth.set_session({'user_id': user.id})
        return redirect('/')
    
    return template('login.html', error='IDまたはパスワードが正しくありません。')

@post('/logout')
def logout_handler():
    auth.delete_session()
    return redirect('/login')

@get('/')
@get('/board')
@auth.login_required
def index():
    # 最初のアクティブなエリアへリダイレクト
    area = Area.select().where(Area.is_active == True).order_by(Area.sort_order).first()
    if not area:
        # エリアが一つもない場合は管理画面へ（adminの場合）
        user = auth.get_current_user()
        if user.role == 'admin':
            return redirect('/admin')
        return "エリアが登録されていません。管理者に連絡してください。"
    return redirect(f'/board/{area.id}')

@get('/board/<area_id:int>')
@auth.login_required
def board_page(area_id):
    user = auth.get_current_user()
    areas = Area.select().where(Area.is_active == True).order_by(Area.sort_order)
    current_area = Area.get_by_id(area_id)
    
    rooms_data = services.get_board_data(area_id)
    statuses = Status.select().where(Status.is_active == True).order_by(Status.sort_order)
    
    return template('board.html', 
                    user=user, 
                    areas=areas, 
                    current_area=current_area, 
                    rooms_data=rooms_data, 
                    statuses=statuses,
                    csrf_token=auth.get_csrf_token(),
                    config=config,
                    current_theme=get_current_theme())

@get('/display/board/<area_id:int>')
def display_board_page(area_id):
    current_area = Area.get_by_id(area_id)
    rooms_data = services.get_board_data(area_id)
    
    return template('display_board.html', 
                    current_area=current_area, 
                    rooms_data=rooms_data,
                    refresh_interval=config.DISPLAY_REFRESH_INTERVAL,
                    now=datetime.datetime.now(),
                    config=config,
                    current_theme=get_current_theme())

@post('/state/room/<room_id:int>')
@auth.role_required('operator')
def update_room_state_handler(room_id):
    if not auth.validate_csrf():
        return "Invalid CSRF Token"
    
    status_id = request.forms.decode().get('status_id')
    user = auth.get_current_user()
    services.update_room_state(room_id, status_id, user)
    
    area_id = request.forms.decode().get('area_id')
    return redirect(f'/board/{area_id}')

@post('/state/bed/<bed_id:int>')
@auth.role_required('operator')
def update_bed_state_handler(bed_id):
    if not auth.validate_csrf():
        return "Invalid CSRF Token"
    
    status_id = request.forms.decode().get('status_id')
    user = auth.get_current_user()
    services.update_bed_state(bed_id, status_id, user)
    
    area_id = request.forms.decode().get('area_id')
    return redirect(f'/board/{area_id}')

@get('/summary')
@get('/summary/<area_id:int>')
@auth.login_required
def summary_page(area_id=None):
    user = auth.get_current_user()
    summary_data = services.get_bed_counts(area_id)
    areas = Area.select().where(Area.is_active == True).order_by(Area.sort_order)
    
    current_area = None
    if area_id:
        current_area = Area.get_by_id(area_id)
        
    return template('summary.html',
                    user=user,
                    areas=areas,
                    current_area=current_area,
                    summary_data=summary_data,
                    config=config,
                    current_theme=get_current_theme())

@get('/theme/<theme_name>')
def switch_theme_handler(theme_name):
    if not config.ALLOW_THEME_SWITCH:
        return redirect('/')
    
    if theme_name not in ['light', 'dark']:
        theme_name = config.DEFAULT_THEME
        
    response.set_cookie('theme', theme_name, path='/')
    
    # 元のページに戻る（リファラがない場合はトップへ）
    referer = request.environ.get('HTTP_REFERER', '/')
    return redirect(referer)

@get('/install')
def install_page():
    if User.select().where(User.role == 'admin').count() > 0:
        return redirect('/login')
    return template('install.html', error=None)

@post('/install')
def install_handler():
    if User.select().where(User.role == 'admin').count() > 0:
        return redirect('/login')
    
    username = request.forms.decode().get('username')
    password = request.forms.decode().get('password')
    confirm = request.forms.decode().get('confirm')
    
    if not username or not password:
        return template('install.html', error='全て入力してください。')
    if password != confirm:
        return template('install.html', error='パスワードが一致しません。')
        
    password_hash, salt = auth.hash_password(password)
    User.create(
        username=username,
        password_hash=password_hash,
        salt=salt,
        role='admin'
    )
    return redirect('/login')
