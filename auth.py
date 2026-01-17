import hashlib
import os
import base64
from bottle import request, response, redirect
from itsdangerous import URLSafeSerializer, BadSignature
import config
from models import User

serializer = URLSafeSerializer(config.SECRET_KEY)

def hash_password(password, salt=None):
    if salt is None:
        salt = os.urandom(16)
    else:
        salt = base64.b64decode(salt)
    
    hash_bytes = hashlib.pbkdf2_hmac(
        'sha256', 
        password.encode('utf-8'), 
        salt, 
        config.HASH_ITERATIONS
    )
    return base64.b64encode(hash_bytes).decode('utf-8'), base64.b64encode(salt).decode('utf-8')

def verify_password(password, salt, stored_hash):
    new_hash, _ = hash_password(password, salt)
    return new_hash == stored_hash

def get_session():
    session_cookie = request.get_cookie(config.SESSION_NAME)
    if not session_cookie:
        return None
    try:
        return serializer.loads(session_cookie)
    except BadSignature:
        return None

def set_session(user_data):
    session_cookie = serializer.dumps(user_data)
    response.set_cookie(config.SESSION_NAME, session_cookie, path='/', httponly=True)

def delete_session():
    response.delete_cookie(config.SESSION_NAME, path='/')

def get_current_user():
    session = get_session()
    if not session or 'user_id' not in session:
        return None
    return User.get_or_none(User.id == session['user_id'], User.is_active == True)

def login_required(callback):
    def wrapper(*args, **kwargs):
        if not get_current_user():
            return redirect('/login')
        return callback(*args, **kwargs)
    return wrapper

def role_required(min_role):
    roles = ['viewer', 'operator', 'admin']
    def decorator(callback):
        def wrapper(*args, **kwargs):
            user = get_current_user()
            if not user:
                return redirect('/login')
            if roles.index(user.role) < roles.index(min_role):
                return "Permission Denied" # Simple error
            return callback(*args, **kwargs)
        return wrapper
    return decorator

# CSRF Protection
def get_csrf_token():
    session = get_session()
    if not session or 'csrf_token' not in session:
        token = hashlib.sha256(os.urandom(32)).hexdigest()
        # セッションを更新
        if session:
            session['csrf_token'] = token
        else:
            session = {'csrf_token': token}
        set_session(session)
        return token
    return session['csrf_token']

def validate_csrf():
    token = request.forms.decode().get('csrf_token')
    session = get_session()
    if not token or not session or token != session.get('csrf_token'):
        return False
    return True
