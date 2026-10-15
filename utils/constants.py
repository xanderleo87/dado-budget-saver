"""Application-wide constants."""

import os

APP_NAME = "Diday"
APP_DISPLAY_NAME = "Diday - Your Budget Saver"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "Your AI Budget Saver"

# Paths - handle both normal Python and PyInstaller frozen mode
import sys
if getattr(sys, 'frozen', False):
    # Running as compiled .exe
    _EXE_DIR = os.path.dirname(sys.executable)
    BASE_DIR = _EXE_DIR
    _INTERNAL_DIR = os.path.join(_EXE_DIR, "_internal")
    ASSETS_DIR = os.path.join(_INTERNAL_DIR, "assets")
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ASSETS_DIR = os.path.join(BASE_DIR, "assets")

DATA_DIR = os.path.join(BASE_DIR, "data")
BACKUP_DIR = os.path.join(DATA_DIR, "backups")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
ICONS_DIR = os.path.join(ASSETS_DIR, "icons")
STYLES_DIR = os.path.join(ASSETS_DIR, "styles")

DB_FILENAME = "finance.db"
ENCRYPTED_DB_PATH = os.path.join(DATA_DIR, DB_FILENAME)

# Currency
DEFAULT_CURRENCY = "PHP"
CURRENCY_SYMBOL = "\u20b1"  # ₱

# Security
BCRYPT_ROUNDS = 12
PBKDF2_ITERATIONS = 100_000
SALT_LENGTH = 16

# AI
DEFAULT_MODEL = "claude-haiku-4-5-20251001"
INSIGHT_MODEL = "claude-haiku-4-5-20251001"
MAX_CONTEXT_MESSAGES = 10
MAX_CONTEXT_EXPENSES = 15

# Timers (milliseconds)
AUTO_SAVE_INTERVAL = 5 * 60 * 1000      # 5 minutes
DEFAULT_REMINDER_INTERVAL = 60           # minutes
DEFAULT_SUMMARY_TIME = "20:00"

# Backup
MAX_BACKUPS = 30

# Default categories: (name, icon, color)
DEFAULT_CATEGORIES = [
    ("Food & Dining", "food", "#FF6BB5"),
    ("Transport", "transport", "#16B5B3"),
    ("Utilities", "utilities", "#7EFFF5"),
    ("Entertainment", "entertainment", "#A78BFA"),
    ("Health", "health", "#34D399"),
    ("Shopping", "shopping", "#FF6BB5"),
    ("Education", "education", "#7EFFF5"),
    ("Housing", "housing", "#FFD23F"),
    ("Personal", "personal", "#C084FC"),
    ("Groceries", "groceries", "#34D399"),
    ("Communication", "communication", "#FB923C"),
    ("Other", "other", "#B8C5D6"),
]

# Coraline-inspired Teal & Pink palette
COLORS = {
    "background": "#0A0E1A",
    "background_alt": "#0D1427",
    "surface": "#1A1E35",
    "surface_solid": "#1A1E35",
    "surface_hover": "#2D1B4E",
    "text": "#F0F4F8",
    "text_dim": "#B8C5D6",
    "accent": "#16B5B3",
    "accent_hover": "#7EFFF5",
    "pink": "#E91E8C",
    "pink_hover": "#FF6BB5",
    "pink_soft": "#FFC4E1",
    "green": "#34D399",
    "red": "#FF4D6D",
    "yellow": "#FFD23F",
    "peach": "#FB923C",
    "purple": "#2D1B4E",
    "purple_light": "#A78BFA",
    "magic_glow": "#7EFFF5",
    "user_bubble": "#16B5B3",
    "assistant_bubble": "#1A1E35",
    "input_bg": "#0D1427",
    "border": "rgba(22, 181, 179, 0.25)",
    "border_pink": "rgba(233, 30, 140, 0.3)",
    "glow_teal": "#16B5B3",
    "glow_pink": "#E91E8C",
}

# Animation constants
ANIMATION_DURATION = 350  # ms
AURORA_FPS = 30
AURORA_ORB_COUNT = 6
AURORA_ORB_ALPHA = 35  # 0-255
