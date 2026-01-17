import os
import secrets

# 基本設定
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, 'ward_board.db')
DEBUG = True

# セキュリティ設定
# 本番環境では環境変数などから固定の値を設定することを推奨
SECRET_KEY = os.environ.get('SECRET_KEY', secrets.token_hex(32))
SESSION_NAME = 'ward_board_session'

# 状態変更時の確認を有効にするか
CONFIRM_STATE_CHANGE = True

# 表示専用モードの設定
DISPLAY_REFRESH_INTERVAL = 30  # 秒

# パスワードハッシュ設定
HASH_ITERATIONS = 100000

# 初期データ設定
INITIAL_STATUSES = [
    {'key': 'vacant', 'label': '空き', 'color_class': 'bg-success', 'icon_class': 'bi-check-circle', 'sort_order': 1},
    {'key': 'occupied', 'label': '使用中', 'color_class': 'bg-danger', 'icon_class': 'bi-person-fill', 'sort_order': 2},
    {'key': 'cleaning', 'label': '清掃中', 'color_class': 'bg-info', 'icon_class': 'bi-stars', 'sort_order': 3},
    {'key': 'hold', 'label': '調整中', 'color_class': 'bg-warning', 'icon_class': 'bi-exclamation-triangle', 'sort_order': 4},
]

# ログ保持期間（0なら無制限）
LOG_RETENTION_DAYS = 90

# 集計設定 (v1.3)
OCCUPIED_STATUS_KEYS = ["occupied"]
VACANT_STATUS_KEYS = ["vacant"]

# --- v1.4 新機能設定 ---

# デフォルト管理者設定
DEFAULT_ADMIN_USER = os.environ.get('DEFAULT_ADMIN_USER', 'admin')
DEFAULT_ADMIN_PASSWORD = os.environ.get('DEFAULT_ADMIN_PASSWORD', 'admin')

# 日付切替の自動リセット設定
AUTO_RESET_ENABLED = False
AUTO_RESET_AT = "04:00"  # ローカル時刻（HH:MM）
AUTO_RESET_RULES = {
    "cleaning": "vacant",
    "hold": "vacant"
}
AUTO_RESET_SCOPE = "all" # "all" | "area"
AUTO_RESET_AREAS = [] # scope="area" の時に対象とするArea IDのリスト
AUTO_RESET_LOG_MODE = "summary" # "summary" | "per_item"

# 画面テーマ設定
DEFAULT_THEME = "light" # "light" | "dark"
ALLOW_THEME_SWITCH = True

# 表示専用モードの強化
DISPLAY_SHOW_UPDATED_AT = True
DISPLAY_COMPACT = False
DISPLAY_HIDE_EMPTY_ROOMS = False
