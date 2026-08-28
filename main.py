"""
VaultX - Secure Local Password Manager.
Application Entry Point.

Tagline: Your passwords. Secured locally.
"""

import sys
import tkinter as tk
from pathlib import Path
import customtkinter as ctk

from app import config
from app.auth import AuthManager
from app.database import DatabaseManager
from app.utils import logger
from ui.login_window import LoginWindow
from ui.main_window import MainWindow

# Set Windows AppUserModelID early so taskbar (launcher) uses custom icon
if sys.platform.startswith("win"):
    try:
        import ctypes
        app_id = f"hasnaintanoli.{config.APP_NAME.lower()}.passwordmanager.{config.APP_VERSION}"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
    except Exception as e:
        logger.warning(f"Could not set AppUserModelID: {e}")


class VaultXApp(ctk.CTk):
    """Root Application Window for VaultX."""

    def __init__(self):
        super().__init__()

        # Configure CustomTkinter Appearance
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title(f"{config.APP_NAME} - {config.APP_TAGLINE}")
        self.geometry("1120x740")
        self.minsize(960, 640)
        self.configure(fg_color=config.COLORS["bg"])

        # Apply app icon to OS titlebar & taskbar
        self._apply_icon()
        self.after(250, self._apply_icon_deferred)

        # Initialize Backend Services
        self.db = DatabaseManager()
        self.auth = AuthManager(self.db)

        self.current_screen = None
        self._show_login_screen()

        # Handle window close event safely
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _apply_icon(self):
        """Loads and sets the application window icon for OS title bar, taskbar, and launcher."""
        try:
            # 1. Native Windows .ico for titlebar and taskbar
            if sys.platform.startswith("win") and config.ICON_ICO_PATH.exists():
                try:
                    self.iconbitmap(str(config.ICON_ICO_PATH))
                except Exception as e:
                    logger.debug(f"iconbitmap initial: {e}")

            # 2. Tkinter iconphoto for Linux / macOS / Tk internal
            if config.ICON_PNG_PATH.exists():
                try:
                    img = tk.PhotoImage(file=str(config.ICON_PNG_PATH))
                    self.iconphoto(True, img)
                    self._icon_ref = img
                except Exception as e:
                    logger.debug(f"iconphoto initial: {e}")
        except Exception as e:
            logger.warning(f"Could not load app icon: {e}")

    def _apply_icon_deferred(self):
        """Re-applies icon after CustomTkinter finished window setup."""
        try:
            if sys.platform.startswith("win") and config.ICON_ICO_PATH.exists():
                self.iconbitmap(str(config.ICON_ICO_PATH))
            if config.ICON_PNG_PATH.exists() and not hasattr(self, "_icon_ref"):
                img = tk.PhotoImage(file=str(config.ICON_PNG_PATH))
                self.iconphoto(True, img)
                self._icon_ref = img
        except Exception:
            pass

    def _show_login_screen(self):
        """Displays Login / Setup Screen."""
        if self.current_screen:
            self.current_screen.destroy()

        self.current_screen = LoginWindow(
            self,
            auth_manager=self.auth,
            on_login_success=self._show_main_screen
        )
        self.current_screen.pack(fill="both", expand=True)

    def _show_main_screen(self):
        """Displays Main Dashboard Screen after successful unlock."""
        if self.current_screen:
            self.current_screen.destroy()

        self.current_screen = MainWindow(
            self,
            auth_manager=self.auth,
            on_lock_cb=self._show_login_screen
        )
        self.current_screen.pack(fill="both", expand=True)

    def _on_close(self):
        """Locks session and terminates application cleanly."""
        try:
            self.auth.lock_vault()
            logger.info("VaultX shut down cleanly.")
        except Exception as e:
            logger.error(f"Error during app shutdown: {e}")
        self.destroy()
        sys.exit(0)


def main():
    """Main entry point."""
    try:
        app = VaultXApp()
        app.mainloop()
    except Exception as e:
        logger.critical(f"Fatal error launching VaultX: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
