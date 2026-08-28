"""
VaultX Configuration module.
Defines constants, paths, design tokens, security parameters, and default settings.
"""

import sys
import os
from pathlib import Path

# Application Metadata
APP_NAME = "VaultX"
APP_TAGLINE = "Your passwords. Secured locally."
APP_VERSION = "1.0.0"

# Paths
if getattr(sys, "frozen", False):
    # Production Mode (Running as standalone .exe or installed application)
    # Store permanent user data in standard OS user AppData directory
    if sys.platform.startswith("win"):
        appdata_root = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
        USER_DATA_DIR = Path(appdata_root) / APP_NAME
    else:
        USER_DATA_DIR = Path.home() / f".{APP_NAME.lower()}"

    DATA_DIR = USER_DATA_DIR / "data"
    EXPORTS_DIR = USER_DATA_DIR / "exports"
    LOGS_DIR = USER_DATA_DIR / "logs"

    # Bundled readonly assets (icons, themes) extracted by PyInstaller
    BASE_DIR = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    ASSETS_DIR = BASE_DIR / "assets"
else:
    # Development Mode (Running from source code repository)
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / "data"
    EXPORTS_DIR = BASE_DIR / "exports"
    LOGS_DIR = BASE_DIR / "logs"
    ASSETS_DIR = BASE_DIR / "assets"

DEFAULT_DB_PATH = DATA_DIR / "vault.db"
DEFAULT_LOG_PATH = LOGS_DIR / "vaultx.log"
ICON_PNG_PATH = ASSETS_DIR / "icon.png"
ICON_ICO_PATH = ASSETS_DIR / "icon.ico"

# Security Parameters
MIN_MASTER_PASSWORD_LENGTH = 12

# Argon2id Parameters (Cryptographically robust parameters)
ARGON2_TIME_COST = 3
ARGON2_MEMORY_COST = 65536  # 64 MB
ARGON2_PARALLELISM = 4
ARGON2_SALT_LEN = 16
ARGON2_KEY_LEN = 32

# Timeouts & Defaults
DEFAULT_AUTO_LOCK_MINUTES = 5
DEFAULT_CLIPBOARD_CLEAR_SECONDS = 30
DEFAULT_GEN_PASSWORD_LENGTH = 20

AUTO_LOCK_OPTIONS = {
    "Never": 0,
    "1 minute": 1,
    "5 minutes": 5,
    "15 minutes": 15,
    "30 minutes": 30
}

CLIPBOARD_OPTIONS = {
    "10 seconds": 10,
    "30 seconds": 30,
    "60 seconds": 60,
    "Never": 0
}

# Categories
CATEGORIES = [
    "Social",
    "Development",
    "Education",
    "Finance",
    "Shopping",
    "Work",
    "Other"
]

# UI Design System - Color Palette
COLORS = {
    "bg": "#0B0D10",
    "surface": "#11151A",
    "surface_hover": "#1A2026",
    "card_bg": "#161B22",
    "primary": "#2563EB",
    "primary_hover": "#1D4ED8",
    "text": "#F8FAFC",
    "muted": "#94A3B8",
    "border": "#1E293B",
    "danger": "#EF4444",
    "danger_hover": "#DC2626",
    "success": "#10B981",
    "warning": "#F59E0B",
    "sidebar_bg": "#0B0D10",
    "input_bg": "#161B22",
    "accent_bg": "#1E293B"
}
