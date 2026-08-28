"""
VaultX Main Application Shell & Window.
Integrates sidebar navigation, real-time search header, auto-lock activity timer,
and view switching.
"""

import time
from typing import Callable, Optional
from PIL import Image
import customtkinter as ctk

from app import config
from app.auth import AuthManager
from ui.components import ModernCard, ToastNotification
from ui.password_generator import PasswordGeneratorView
from ui.settings import SettingsView
from ui.vault_view import VaultView


class MainWindow(ctk.CTkFrame):
    """Main application shell holding sidebar navigation, search bar, and view container."""

    def __init__(self, master, auth_manager: AuthManager, on_lock_cb: Callable[[], None]):
        super().__init__(master, fg_color=config.COLORS["bg"])
        self.auth = auth_manager
        self.on_lock_cb = on_lock_cb

        self.last_activity_time = time.time()
        self.auto_lock_timer_id = None
        self.current_active_nav = "all"

        self._build_ui()
        self._start_autolock_monitor()

        # Bind user activity events to reset auto-lock countdown timer
        master.bind_all("<Any-KeyPress>", self._reset_activity_timer)
        master.bind_all("<Any-ButtonPress>", self._reset_activity_timer)
        master.bind_all("<Motion>", self._reset_activity_timer)

    def _build_ui(self):
        # 1. Left Sidebar Navigation Frame
        self.sidebar = ctk.CTkFrame(self, width=240, fg_color=config.COLORS["sidebar_bg"], corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # App Brand Header
        brand_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand_frame.pack(fill="x", padx=16, pady=(18, 12))

        # Brand title & logo row
        brand_row = ctk.CTkFrame(brand_frame, fg_color="transparent")
        brand_row.pack(fill="x")

        if config.ICON_PNG_PATH.exists():
            try:
                pil_icon = Image.open(config.ICON_PNG_PATH)
                self.sidebar_logo_img = ctk.CTkImage(light_image=pil_icon, dark_image=pil_icon, size=(30, 30))
                icon_lbl = ctk.CTkLabel(brand_row, image=self.sidebar_logo_img, text="")
                icon_lbl.pack(side="left", padx=(0, 10))
            except Exception:
                pass

        ctk.CTkLabel(
            brand_row,
            text="VaultX",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=config.COLORS["text"]
        ).pack(side="left")

        ctk.CTkLabel(
            brand_frame,
            text=config.APP_TAGLINE,
            font=ctk.CTkFont(size=11),
            text_color=config.COLORS["muted"]
        ).pack(anchor="w", pady=(4, 0))

        # Thin separator
        ctk.CTkFrame(self.sidebar, height=1, fg_color=config.COLORS["border"]).pack(fill="x", padx=16, pady=(0, 8))

        # Main Nav Buttons — packed directly into sidebar with tight spacing
        self.btn_all = self._create_nav_button("🏠  All Items", lambda: self._navigate_to("all"))
        self.btn_all.pack(fill="x", padx=10, pady=2)

        self.btn_fav = self._create_nav_button("⭐  Favorites", lambda: self._navigate_to("favorites"))
        self.btn_fav.pack(fill="x", padx=10, pady=2)

        self.btn_gen = self._create_nav_button("🔑  Generator", lambda: self._navigate_to("generator"))
        self.btn_gen.pack(fill="x", padx=10, pady=2)

        self.btn_settings = self._create_nav_button("⚙  Settings", lambda: self._navigate_to("settings"))
        self.btn_settings.pack(fill="x", padx=10, pady=2)

        # Thin separator before categories
        ctk.CTkFrame(self.sidebar, height=1, fg_color=config.COLORS["border"]).pack(fill="x", padx=16, pady=(10, 8))

        # Categories Section Header
        ctk.CTkLabel(
            self.sidebar,
            text="CATEGORIES",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=config.COLORS["muted"]
        ).pack(anchor="w", padx=20, pady=(0, 4))

        # Category nav buttons
        self.cat_buttons = {}
        for cat in config.CATEGORIES:
            btn = self._create_nav_button(f"📁  {cat}", lambda c=cat: self._navigate_to(f"cat_{c}"))
            btn.pack(fill="x", padx=10, pady=1)
            self.cat_buttons[cat] = btn

        # Sidebar Footer Status & Lock Button
        side_footer = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        side_footer.pack(side="bottom", fill="x", padx=16, pady=20)

        ctk.CTkButton(
            side_footer,
            text="🔒 Lock Vault",
            height=38,
            fg_color=config.COLORS["accent_bg"],
            hover_color=config.COLORS["surface_hover"],
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._manual_lock
        ).pack(fill="x")

        # 2. Main Content Area Frame
        self.main_content = ctk.CTkFrame(self, fg_color="transparent")
        self.main_content.pack(side="right", fill="both", expand=True)

        # Top Header Bar (Search Input + Add Button)
        self.header_bar = ctk.CTkFrame(self.main_content, height=64, fg_color=config.COLORS["surface"], corner_radius=0)
        self.header_bar.pack(fill="x")
        self.header_bar.pack_propagate(False)

        # Search Box
        self.search_entry = ctk.CTkEntry(
            self.header_bar,
            placeholder_text="🔍 Search your vault (Title, Username, URL, Category)...",
            height=38,
            width=360,
            fg_color=config.COLORS["input_bg"],
            border_color=config.COLORS["border"]
        )
        self.search_entry.pack(side="left", padx=20, pady=13)
        self.search_entry.bind("<KeyRelease>", self._on_search_key_release)

        # Add Item Button
        self.add_btn = ctk.CTkButton(
            self.header_bar,
            text="+ Add Item",
            height=38,
            width=120,
            fg_color=config.COLORS["primary"],
            hover_color=config.COLORS["primary_hover"],
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._open_add_dialog
        )
        self.add_btn.pack(side="right", padx=20, pady=13)

        # View Container
        self.view_container = ctk.CTkFrame(self.main_content, fg_color="transparent")
        self.view_container.pack(fill="both", expand=True)

        # Instantiate View Instances
        self.vault_view = VaultView(self.view_container, self.auth, on_vault_updated_cb=self._on_vault_updated)
        self.generator_view = PasswordGeneratorView(self.view_container, self.auth)
        self.settings_view = SettingsView(self.view_container, self.auth, on_settings_changed_cb=self._on_settings_changed)

        # Initial Navigation
        self._navigate_to("all")

    def _create_nav_button(self, text: str, command: Callable) -> ctk.CTkButton:
        return ctk.CTkButton(
            self.sidebar,
            text=text,
            anchor="w",
            height=36,
            fg_color="transparent",
            hover_color=config.COLORS["surface_hover"],
            text_color=config.COLORS["text"],
            font=ctk.CTkFont(size=13),
            command=command
        )

    def _navigate_to(self, nav_target: str):
        """Switches active view and highlights corresponding navigation button."""
        self.current_active_nav = nav_target

        # Hide all views
        self.vault_view.pack_forget()
        self.generator_view.pack_forget()
        self.settings_view.pack_forget()

        # Reset button highlight states
        for btn in [self.btn_all, self.btn_fav, self.btn_gen, self.btn_settings] + list(self.cat_buttons.values()):
            btn.configure(fg_color="transparent")

        if nav_target == "all":
            self.btn_all.configure(fg_color=config.COLORS["accent_bg"])
            self.vault_view.set_filter(category=None, favorites_only=False, search_query=self.search_entry.get())
            self.vault_view.pack(fill="both", expand=True)
        elif nav_target == "favorites":
            self.btn_fav.configure(fg_color=config.COLORS["accent_bg"])
            self.vault_view.set_filter(category=None, favorites_only=True, search_query=self.search_entry.get())
            self.vault_view.pack(fill="both", expand=True)
        elif nav_target == "generator":
            self.btn_gen.configure(fg_color=config.COLORS["accent_bg"])
            self.generator_view.pack(fill="both", expand=True)
        elif nav_target == "settings":
            self.btn_settings.configure(fg_color=config.COLORS["accent_bg"])
            self.settings_view.pack(fill="both", expand=True)
        elif nav_target.startswith("cat_"):
            cat_name = nav_target.replace("cat_", "")
            if cat_name in self.cat_buttons:
                self.cat_buttons[cat_name].configure(fg_color=config.COLORS["accent_bg"])
            self.vault_view.set_filter(category=cat_name, favorites_only=False, search_query=self.search_entry.get())
            self.vault_view.pack(fill="both", expand=True)

    def _on_search_key_release(self, event=None):
        """Updates vault search query dynamically on keypress."""
        query = self.search_entry.get()
        if self.current_active_nav not in ["generator", "settings"]:
            self.vault_view.set_filter(
                category=self.vault_view.current_filter_category,
                favorites_only=self.vault_view.favorites_only,
                search_query=query
            )

    def _open_add_dialog(self):
        self.vault_view.open_add_dialog()

    def _on_vault_updated(self):
        self.vault_view.refresh_vault()

    def _on_settings_changed(self):
        self.vault_view.refresh_vault()

    def _reset_activity_timer(self, event=None):
        """Resets inactivity timestamp whenever user interacts with the app."""
        self.last_activity_time = time.time()

    def _start_autolock_monitor(self):
        """Periodically checks inactivity duration against auto-lock settings."""
        self._check_autolock()

    def _check_autolock(self):
        if not self.auth.is_unlocked():
            return

        minutes_setting = int(self.auth.db.get_setting("auto_lock_minutes", str(config.DEFAULT_AUTO_LOCK_MINUTES)))
        if minutes_setting > 0:
            elapsed_seconds = time.time() - self.last_activity_time
            timeout_seconds = minutes_setting * 60

            if elapsed_seconds >= timeout_seconds:
                self._trigger_autolock()
                return

        # Schedule next check in 2 seconds
        self.auto_lock_timer_id = self.after(2000, self._check_autolock)

    def _trigger_autolock(self):
        """Locks vault due to inactivity timeout."""
        self.auth.lock_vault()
        ToastNotification(self.winfo_toplevel(), "Vault automatically locked due to inactivity.", is_error=False)
        self.on_lock_cb()

    def _manual_lock(self):
        """Manually locks vault on button click."""
        self.auth.lock_vault()
        self.on_lock_cb()
