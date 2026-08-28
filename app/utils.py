"""
VaultX Utility Functions.
Provides logging setup, clipboard management with timed auto-clear,
URL formatting, and general helper functions.
"""

import logging
import os
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable

import pyperclip
from app import config


def setup_logging(log_file: Optional[Path] = None) -> logging.Logger:
    """
    Sets up application logging safely.
    Logs developer diagnostics to a log file WITHOUT logging sensitive passwords or keys.
    """
    target_path = log_file or config.DEFAULT_LOG_PATH
    target_path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("VaultX")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        file_handler = logging.FileHandler(target_path, encoding="utf-8")
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger


logger = setup_logging()


class ClipboardManager:
    """
    Manages system clipboard operations with automatic timed clearing
    to prevent password exposure in clipboard history.
    """
    _timer: Optional[threading.Timer] = None
    _last_copied_text: Optional[str] = None

    @classmethod
    def copy_with_autoclear(cls, text: str, clear_after_seconds: int = 30, on_clear_cb: Optional[Callable] = None):
        """
        Copies text to system clipboard and schedules automatic clearing after clear_after_seconds.
        """
        if not text:
            return

        # Cancel previous timer if pending
        if cls._timer:
            cls._timer.cancel()
            cls._timer = None

        try:
            pyperclip.copy(text)
            cls._last_copied_text = text
            logger.info("Copied sensitive data to clipboard.")
        except Exception as e:
            logger.error(f"Failed to copy to clipboard via pyperclip: {e}")

        if clear_after_seconds > 0:
            cls._timer = threading.Timer(
                clear_after_seconds,
                cls._clear_if_matches,
                args=(text, on_clear_cb)
            )
            cls._timer.daemon = True
            cls._timer.start()

    @classmethod
    def _clear_if_matches(cls, expected_text: str, on_clear_cb: Optional[Callable] = None):
        """Clears clipboard if current content matches what was copied."""
        try:
            current = pyperclip.paste()
            if current == expected_text or cls._last_copied_text == expected_text:
                pyperclip.copy("")
                cls._last_copied_text = None
                logger.info("Clipboard automatically cleared for security.")
                if on_clear_cb:
                    on_clear_cb()
        except Exception as e:
            logger.error(f"Error during clipboard auto-clear: {e}")


def format_iso_datetime(dt: Optional[datetime] = None) -> str:
    """Returns ISO 8601 formatted datetime string."""
    if dt is None:
        dt = datetime.now()
    return dt.isoformat()


def format_display_date(iso_str: str) -> str:
    """Converts ISO 8601 string to a readable date format."""
    if not iso_str:
        return ""
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime("%b %d, %Y %I:%M %p")
    except Exception:
        return iso_str


def sanitize_url(url: str) -> str:
    """Formats URL to include http/https if missing for valid browser opening."""
    url = url.strip()
    if not url:
        return ""
    if not (url.startswith("http://") or url.startswith("https://")):
        return f"https://{url}"
    return url
