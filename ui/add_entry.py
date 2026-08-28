"""
VaultX Add Entry Modal Dialog.
Provides a modern form to create and encrypt new password/note items.
"""

import customtkinter as ctk
from typing import Callable

from app import config
from app.auth import AuthManager
from app.models import VaultEntry
from app.password_generator import generate_password
from ui.components import ModernCard, ToastNotification


class AddEntryDialog(ctk.CTkToplevel):
    """Modal dialog for creating a new vault item."""

    def __init__(self, master, auth_manager: AuthManager, on_saved_cb: Callable[[], None]):
        super().__init__(master)
        self.title("Add New Item - VaultX")
        self.geometry("520x680")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.grab_set()

        self.configure(fg_color=config.COLORS["bg"])
        self.auth = auth_manager
        self.on_saved_cb = on_saved_cb
        self.show_pass = False

        self._build_ui()

    def _build_ui(self):
        card = ModernCard(self)
        card.pack(fill="both", expand=True, padx=16, pady=16)

        # Header
        ctk.CTkLabel(
            card,
            text="Add Password Entry",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=config.COLORS["text"]
        ).pack(anchor="w", padx=20, pady=(20, 16))

        scrollable = ctk.CTkScrollableFrame(card, fg_color="transparent")
        scrollable.pack(fill="both", expand=True, padx=12, pady=(0, 10))

        # Title
        ctk.CTkLabel(scrollable, text="Title *", font=ctk.CTkFont(size=12, weight="bold"), text_color=config.COLORS["text"]).pack(anchor="w", pady=(4, 2))
        self.title_entry = ctk.CTkEntry(scrollable, placeholder_text="e.g. GitHub, Google, Work Email", height=38, fg_color=config.COLORS["input_bg"], border_color=config.COLORS["border"])
        self.title_entry.pack(fill="x", pady=(0, 12))

        # Username / Email
        ctk.CTkLabel(scrollable, text="Username / Email", font=ctk.CTkFont(size=12, weight="bold"), text_color=config.COLORS["text"]).pack(anchor="w", pady=(4, 2))
        self.username_entry = ctk.CTkEntry(scrollable, placeholder_text="e.g. alex@example.com", height=38, fg_color=config.COLORS["input_bg"], border_color=config.COLORS["border"])
        self.username_entry.pack(fill="x", pady=(0, 12))

        # Password
        ctk.CTkLabel(scrollable, text="Password *", font=ctk.CTkFont(size=12, weight="bold"), text_color=config.COLORS["text"]).pack(anchor="w", pady=(4, 2))
        pass_frame = ctk.CTkFrame(scrollable, fg_color="transparent")
        pass_frame.pack(fill="x", pady=(0, 12))

        self.password_entry = ctk.CTkEntry(pass_frame, show="•", placeholder_text="Enter password...", height=38, fg_color=config.COLORS["input_bg"], border_color=config.COLORS["border"])
        self.password_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self.eye_btn = ctk.CTkButton(pass_frame, text="👁", width=38, height=38, fg_color=config.COLORS["accent_bg"], hover_color=config.COLORS["surface_hover"], command=self._toggle_pass)
        self.eye_btn.pack(side="left", padx=(0, 6))

        self.gen_btn = ctk.CTkButton(pass_frame, text="Generate", width=90, height=38, fg_color=config.COLORS["primary"], hover_color=config.COLORS["primary_hover"], command=self._quick_generate_pass)
        self.gen_btn.pack(side="right")

        # Website URL
        ctk.CTkLabel(scrollable, text="Website URL", font=ctk.CTkFont(size=12, weight="bold"), text_color=config.COLORS["text"]).pack(anchor="w", pady=(4, 2))
        self.url_entry = ctk.CTkEntry(scrollable, placeholder_text="https://github.com", height=38, fg_color=config.COLORS["input_bg"], border_color=config.COLORS["border"])
        self.url_entry.pack(fill="x", pady=(0, 12))

        # Category Dropdown
        ctk.CTkLabel(scrollable, text="Category", font=ctk.CTkFont(size=12, weight="bold"), text_color=config.COLORS["text"]).pack(anchor="w", pady=(4, 2))
        self.category_opt = ctk.CTkOptionMenu(scrollable, values=config.CATEGORIES, height=38, fg_color=config.COLORS["input_bg"], button_color=config.COLORS["accent_bg"], button_hover_color=config.COLORS["surface_hover"])
        self.category_opt.set("Development")
        self.category_opt.pack(fill="x", pady=(0, 12))

        # Favorite Checkbox
        self.fav_var = ctk.BooleanVar(value=False)
        self.fav_cb = ctk.CTkCheckBox(scrollable, text="Mark as Favorite ⭐", variable=self.fav_var, text_color=config.COLORS["text"], fg_color=config.COLORS["primary"], hover_color=config.COLORS["primary_hover"])
        self.fav_cb.pack(anchor="w", pady=(4, 12))

        # Notes
        ctk.CTkLabel(scrollable, text="Notes", font=ctk.CTkFont(size=12, weight="bold"), text_color=config.COLORS["text"]).pack(anchor="w", pady=(4, 2))
        self.notes_text = ctk.CTkTextbox(scrollable, height=90, fg_color=config.COLORS["input_bg"], border_color=config.COLORS["border"], border_width=1)
        self.notes_text.pack(fill="x", pady=(0, 12))

        # Error label
        self.error_label = ctk.CTkLabel(card, text="", font=ctk.CTkFont(size=12), text_color=config.COLORS["danger"])
        self.error_label.pack(anchor="w", padx=20, pady=(0, 4))

        # Buttons Frame
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(fill="x", side="bottom", padx=20, pady=(0, 20))

        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            fg_color=config.COLORS["accent_bg"],
            hover_color=config.COLORS["surface_hover"],
            text_color=config.COLORS["text"],
            height=40,
            width=110,
            command=self._close_dialog
        ).pack(side="left")

        ctk.CTkButton(
            btn_frame,
            text="Save Password",
            fg_color=config.COLORS["primary"],
            hover_color=config.COLORS["primary_hover"],
            font=ctk.CTkFont(size=13, weight="bold"),
            height=40,
            width=140,
            command=self._save_entry
        ).pack(side="right")

    def _close_dialog(self):
        try:
            self.grab_release()
        except Exception:
            pass
        self.after(30, self.destroy)

    def _toggle_pass(self):
        self.show_pass = not self.show_pass
        if self.show_pass:
            self.password_entry.configure(show="")
            self.eye_btn.configure(text="🙈")
        else:
            self.password_entry.configure(show="•")
            self.eye_btn.configure(text="👁")

    def _quick_generate_pass(self):
        pwd = generate_password(length=20, use_uppercase=True, use_lowercase=True, use_numbers=True, use_symbols=True)
        self.password_entry.delete(0, "end")
        self.password_entry.insert(0, pwd)
        self.password_entry.configure(show="")
        self.show_pass = True
        self.eye_btn.configure(text="🙈")
        ToastNotification(self.winfo_toplevel(), "Generated secure password!", is_error=False)

    def _save_entry(self):
        title = self.title_entry.get().strip()
        pwd = self.password_entry.get()
        username = self.username_entry.get().strip()
        url = self.url_entry.get().strip()
        category = self.category_opt.get()
        notes = self.notes_text.get("1.0", "end-1c").strip()
        favorite = self.fav_var.get()

        if not title:
            self.error_label.configure(text="Please provide an item title.")
            return

        if not pwd:
            self.error_label.configure(text="Please provide or generate a password.")
            return

        entry = VaultEntry(
            title=title,
            username=username,
            password=pwd,
            url=url,
            notes=notes,
            category=category,
            favorite=favorite
        )

        try:
            encrypted_data = self.auth.encrypt_entry(entry)
            self.auth.db.add_entry(encrypted_data)
            ToastNotification(self.master, f"Added '{title}' to vault!", is_error=False)
            self._close_dialog()
            if self.on_saved_cb:
                self.on_saved_cb()
        except Exception as e:
            self.error_label.configure(text=f"Failed to save entry: {e}")
