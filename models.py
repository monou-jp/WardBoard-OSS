from peewee import *
import datetime
import config

db = SqliteDatabase(None)

class BaseModel(Model):
    created_at = DateTimeField(default=datetime.datetime.now)
    updated_at = DateTimeField(default=None, null=True)

    def save(self, *args, **kwargs):
        self.updated_at = datetime.datetime.now()
        return super(BaseModel, self).save(*args, **kwargs)

    class Meta:
        database = db

class User(BaseModel):
    username = CharField(unique=True)
    password_hash = CharField()
    salt = CharField()
    role = CharField()  # viewer, operator, admin
    is_active = BooleanField(default=True)

class Area(BaseModel):
    name = CharField()
    sort_order = IntegerField(default=0)
    is_active = BooleanField(default=True)

class Room(BaseModel):
    area = ForeignKeyField(Area, backref='rooms')
    code = CharField()
    name = CharField()
    sort_order = IntegerField(default=0)
    is_active = BooleanField(default=True)

class Bed(BaseModel):
    room = ForeignKeyField(Room, backref='beds')
    code = CharField()
    name = CharField()
    sort_order = IntegerField(default=0)
    is_active = BooleanField(default=True)
    is_available = BooleanField(default=True)

class Status(BaseModel):
    key = CharField(unique=True)
    label = CharField()
    color_class = CharField()  # Bootstrap class (bg-success, etc.)
    icon_class = CharField()   # Bootstrap Icons class
    sort_order = IntegerField(default=0)
    is_active = BooleanField(default=True)
    applies_to_room = BooleanField(default=True)
    applies_to_bed = BooleanField(default=True)

class RoomState(BaseModel):
    room = ForeignKeyField(Room, unique=True, backref='state')
    status = ForeignKeyField(Status)
    updated_by = ForeignKeyField(User, null=True)
    note = TextField(null=True)

class BedState(BaseModel):
    bed = ForeignKeyField(Bed, unique=True, backref='state')
    status = ForeignKeyField(Status)
    updated_by = ForeignKeyField(User, null=True)
    note = TextField(null=True)

class StateChangeLog(BaseModel):
    target_type = CharField()  # 'room' or 'bed'
    room = ForeignKeyField(Room, null=True, backref='logs')
    bed = ForeignKeyField(Bed, null=True, backref='logs')
    area = ForeignKeyField(Area, null=True, backref='logs')
    from_status = ForeignKeyField(Status, null=True, related_name='logs_from')
    to_status = ForeignKeyField(Status, null=True, related_name='logs_to')
    changed_by = ForeignKeyField(User, null=True)
    changed_at = DateTimeField(default=datetime.datetime.now)
    note = TextField(null=True)
    meta = TextField(null=True)

class SystemJobState(BaseModel):
    job_key = CharField(unique=True)
    last_run_at = DateTimeField(null=True)
    last_run_date = DateField(null=True)

def init_db(database_path=None):
    import auth
    if database_path:
        db.init(database_path)
    else:
        db.init(config.DATABASE)
        
    db.connect(reuse_if_open=True)
    db.create_tables([User, Area, Room, Bed, Status, RoomState, BedState, StateChangeLog, SystemJobState])
    
    # 初期ステータスの投入
    if Status.select().count() == 0:
        for s in config.INITIAL_STATUSES:
            Status.create(**s)
            
    # 初期管理者の投入
    if User.select().where(User.role == 'admin').count() == 0:
        # 循環参照を避けるために init_db 内でインポート
        from auth import hash_password
        password_hash, salt = hash_password(config.DEFAULT_ADMIN_PASSWORD)
        User.create(
            username=config.DEFAULT_ADMIN_USER,
            password_hash=password_hash,
            salt=salt,
            role='admin'
        )
        
    db.close()
