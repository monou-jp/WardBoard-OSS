#!/usr/local/bin/python3

import os
import sys
from bottle import Bottle, run, static_file, redirect, TEMPLATE_PATH
import config
import models
import auth
import views_public
import views_admin

def create_app(database_path=None):
    models.init_db(database_path)
    
    if config.BASE_DIR not in TEMPLATE_PATH:
        TEMPLATE_PATH.insert(0, config.BASE_DIR)
    if os.path.join(config.BASE_DIR, 'templates') not in TEMPLATE_PATH:
        TEMPLATE_PATH.insert(0, os.path.join(config.BASE_DIR, 'templates'))
    
    app = Bottle()

    # 静的ファイルの配信
    @app.get('/static/<path:path>')
    def server_static(path):
        return static_file(path, root=os.path.join(config.BASE_DIR, 'static'))

    @app.route('/api/version')
    def api_version():
        return {
            "version": "1.4",
            "system": "WardBoard-OSS",
            "status": "OK"
        }

    # ルーティングの統合
    app.add_hook('before_request', views_public.before_request)
    app.route('/login', 'GET', views_public.login_page)
    app.route('/login', 'POST', views_public.login_handler)
    app.route('/logout', 'POST', views_public.logout_handler)
    app.route('/', 'GET', views_public.index)
    app.route('/board', 'GET', views_public.index)
    app.route('/board/<area_id:int>', 'GET', views_public.board_page)
    app.route('/state/room/<room_id:int>', 'POST', views_public.update_room_state_handler)
    app.route('/state/bed/<bed_id:int>', 'POST', views_public.update_bed_state_handler)
    app.route('/summary', 'GET', views_public.summary_page)
    app.route('/summary/<area_id:int>', 'GET', views_public.summary_page)
    app.route('/install', 'GET', views_public.install_page)
    app.route('/install', 'POST', views_public.install_handler)

    # 管理画面の統合
    app.get('/admin')(views_admin.admin_index)
    app.get('/admin/areas')(views_admin.admin_areas)
    app.get('/admin/areas/new')(views_admin.admin_areas_new)
    app.post('/admin/areas/new')(views_admin.admin_areas_create)
    app.get('/admin/areas/<id:int>/edit')(views_admin.admin_areas_edit)
    app.post('/admin/areas/<id:int>/edit')(views_admin.admin_areas_update)
    app.post('/admin/areas/<id:int>/toggle_active')(views_admin.admin_areas_toggle)

    app.get('/admin/rooms')(views_admin.admin_rooms)
    app.get('/admin/rooms/new')(views_admin.admin_rooms_new)
    app.post('/admin/rooms/new')(views_admin.admin_rooms_create)
    app.get('/admin/rooms/<id:int>/edit')(views_admin.admin_rooms_edit)
    app.post('/admin/rooms/<id:int>/edit')(views_admin.admin_rooms_update)
    app.post('/admin/rooms/<id:int>/toggle_active')(views_admin.admin_rooms_toggle)

    app.get('/admin/beds')(views_admin.admin_beds)
    app.get('/admin/beds/new')(views_admin.admin_beds_new)
    app.post('/admin/beds/new')(views_admin.admin_beds_create)
    app.get('/admin/beds/<id:int>/edit')(views_admin.admin_beds_edit)
    app.post('/admin/beds/<id:int>/edit')(views_admin.admin_beds_update)
    app.post('/admin/beds/<id:int>/toggle_active')(views_admin.admin_beds_toggle)

    app.get('/admin/statuses')(views_admin.admin_statuses)
    app.get('/admin/statuses/new')(views_admin.admin_statuses_new)
    app.post('/admin/statuses/new')(views_admin.admin_statuses_create)
    app.get('/admin/statuses/<id:int>/edit')(views_admin.admin_statuses_edit)
    app.post('/admin/statuses/<id:int>/edit')(views_admin.admin_statuses_update)

    app.get('/admin/users')(views_admin.admin_users)
    app.get('/admin/users/new')(views_admin.admin_users_new)
    app.post('/admin/users/new')(views_admin.admin_users_create)
    app.get('/admin/users/<id:int>/edit')(views_admin.admin_users_edit)
    app.post('/admin/users/<id:int>/edit')(views_admin.admin_users_update)
    app.post('/admin/users/<id:int>/toggle_active')(views_admin.admin_users_toggle)
    
    app.get('/admin/logs')(views_admin.admin_logs)
    app.post('/admin/logs/purge')(views_admin.admin_logs_purge)
    
    app.get('/display/board/<area_id:int>')(views_public.display_board_page)
    app.get('/theme/<theme_name>')(views_public.switch_theme_handler)
    
    return app

# 初期化
if __name__ == '__main__':
    app = create_app()

    if os.path.exists("dev.flag"):
        run(app, host='localhost', port=8080, debug=config.DEBUG, reloader=config.DEBUG)
    else:
        run(app, server='cgi')
else:
    # WSGI用
    application = create_app()
