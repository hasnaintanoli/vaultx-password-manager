"""
VaultX View / Edit Entry Modal Dialog.
Provides viewing, password copying with auto-clear, editing, favoriting, and secure deletion.
"""

import webbrowser
import customtkinter as ctk
from typing import Callable

from app import config
from app.auth import AuthManager
from app.models import VaultEntry
from app.password_generator import generate_password, evaluate_password_strength
from app.utils import ClipboardManager, sanitize_url, format_display_date
from ui.components import ModernCard, CategoryBadge, ConfirmDialog, ToastNotification, PasswordStrengthBar


class EditEntryDialog(ctk.CTkToplevel):
    """Modal dialog for viewing, editing, and deleting a vault entry."""

    def __init__(self, master, auth_manager: AuthManager, entry: VaultEntry, on_changed_cb: Callable[[], None]):
        super().__init__(master)
        self.title(f"{entry.title} - VaultX")
        self.geometry("540x700")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.grab_set()

        self.configure(fg_color=config.COLORS["bg"])
        self.auth = auth_manager
        self.entry = entry
        self.on_changed_cb = on_changed_cb

        self.is_edit_mode = False
        self.show_pass = False

        self._build_ui()

    def _build_ui(self):
        card = ModernCard(self)
        card.pack(fill="both", expand=True, padx=16, pady=16)

        # Header Row (Title + Favorite Star)
        header_frame = ctk.CTkFrame(card, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(20, 10))

        self.title_lbl = ctk.CTkLabel(
            header_frame,
            text=self.entry.title,
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=config.COLORS["text"]
        )
        self.title_lbl.pack(side="left")

        star_symbol = "⭐" if self.entry.favorite else "☆"
        self.fav_btn = ctk.CTkButton(
            header_frame,
            text=star_symbol,
            width=36,
            height=36,
            fg_color="transparent",
            hover_color=config.COLORS["surface_hover"],
            font=ctk.CTkFont(size=18),
            command=self._toggle_favorite
        )
        self.fav_btn.pack(side="right")

        CategoryBadge(header_frame, text=self.entry.category).pack(side="right", padx=(0, 10))

        scrollable = ctk.CTkScrollableFrame(card, fg_color="transparent")
        scrollable.pack(fill="both", expand=True, padx=12, pady=(0, 10))

        # Title Field (Editable)
        ctk.CTkLabel(scrollable, text="Title", font=ctk.CTkFont(size=12, weight="bold"), text_color=config.COLORS["muted"]).pack(anchor="w", pady=(6, 2))
        self.title_entry = ctk.CTkEntry(scrollable, height=38, fg_color=config.COLORS["input_bg"], border_color=config.COLORS["border"])
        self.title_entry.insert(0, self.entry.title)
        self.title_entry.pack(fill="x", pady=(0, 10))

        # Username / Email
        ctk.CTkLabel(scrollable, text="Username / Email", font=ctk.CTkFont(size=12, weight="bold"), text_color=config.COLORS["muted"]).pack(anchor="w", pady=(6, 2))
        user_frame = ctk.CTkFrame(scrollable, fg_color="transparent")
        user_frame.pack(fill="x", pady=(0, 10))

        self.user_entry = ctk.CTkEntry(user_frame, height=38, fg_color=config.COLORS["input_bg"], border_color=config.COLORS["border"])
        self.user_entry.insert(0, self.entry.username)
        self.user_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))

        ctk.CTkButton(user_frame, text="📋", width=38, height=38, fg_color=config.COLORS["accent_bg"], hover_color=config.COLORS["surface_hover"], command=self._copy_username).pack(side="right")

        # Password
        ctk.CTkLabel(scrollable, text="Password", font=ctk.CTkFont(size=12, weight="bold"), text_color=config.COLORS["muted"]).pack(anchor="w", pady=(6, 2))
        pass_frame = ctk.CTkFrame(scrollable, fg_color="transparent")
        pass_frame.pack(fill="x", pady=(0, 6))

        self.pass_entry = ctk.CTkEntry(pass_frame, show="•", height=38, fg_color=config.COLORS["input_bg"], border_color=config.COLORS["border"])
        self.pass_entry.insert(0, self.entry.password)
        self.pass_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self.pass_entry.bind("<KeyRelease>", self._on_password_change)

        self.eye_btn = ctk.CTkButton(pass_frame, text="👁", width=38, height=38, fg_color=config.COLORS["accent_bg"], hover_color=config.COLORS["surface_hover"], command=self._toggle_pass)
        self.eye_btn.pack(side="left", padx=(0, 6))

        ctk.CTkButton(pass_frame, text="📋", width=38, height=38, fg_color=config.COLORS["accent_bg"], hover_color=config.COLORS["surface_hover"], command=self._copy_password).pack(side="left", padx=(0, 6))

        self.gen_btn = ctk.CTkButton(pass_frame, text="Generate", width=80, height=38, fg_color=config.COLORS["primary"], hover_color=config.COLORS["primary_hover"], command=self._generate_pass)
        self.gen_btn.pack(side="right")

        # Strength Bar
        self.strength_bar = PasswordStrengthBar(scrollable)
        self.strength_bar.pack(fill="x", pady=(0, 10))
        self._update_strength_display()

        # Website
        ctk.CTkLabel(scrollable, text="Website URL", font=ctk.CTkFont(size=12, weight="bold"), text_color=config.COLORS["muted"]).pack(anchor="w", pady=(6, 2))
        web_frame = ctk.CTkFrame(scrollable, fg_color="transparent")
        web_frame.pack(fill="x", pady=(0, 10))

        self.url_entry = ctk.CTkEntry(web_frame, height=38, fg_color=config.COLORS["input_bg"], border_color=config.COLORS["border"])
        self.url_entry.insert(0, self.entry.url)
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))

        ctk.CTkButton(web_frame, text="🌐 Launch", width=80, height=38, fg_color=config.COLORS["accent_bg"], hover_color=config.COLORS["surface_hover"], command=self._open_url).pack(side="right")

        # Category
        ctk.CTkLabel(scrollable, text="Category", font=ctk.CTkFont(size=12, weight="bold"), text_color=config.COLORS["muted"]).pack(anchor="w", pady=(6, 2))
        self.category_opt = ctk.CTkOptionMenu(scrollable, values=config.CATEGORIES, height=38, fg_color=config.COLORS["input_bg"], button_color=config.COLORS["accent_bg"], button_hover_color=config.COLORS["surface_hover"])
        self.category_opt.set(self.entry.category)
        self.category_opt.pack(fill="x", pady=(0, 10))

        # Notes
        ctk.CTkLabel(scrollable, text="Notes", font=ctk.CTkFont(size=12, weight="bold"), text_color=config.COLORS["muted"]).pack(anchor="w", pady=(6, 2))
        self.notes_text = ctk.CTkTextbox(scrollable, height=80, fg_color=config.COLORS["input_bg"], border_color=config.COLORS["border"], border_width=1)
        self.notes_text.insert("1.0", self.entry.notes)
        self.notes_text.pack(fill="x", pady=(0, 10))

        # Date Info
        meta_str = f"Created: {format_display_date(self.entry.created_at)}  •  Updated: {format_display_date(self.entry.updated_at)}"
        ctk.CTkLabel(scrollable, text=meta_str, font=ctk.CTkFont(size=11), text_color=config.COLORS["muted"]).pack(anchor="w", pady=(4, 10))

        # Initial view state: set fields to read-only until Edit clicked
        self._set_read_only(True)

        # Footer Action Bar
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(fill="x", side="bottom", padx=20, pady=(0, 20))

        ctk.CTkButton(
            btn_frame,
            text="Delete",
            fg_color=config.COLORS["danger"],
            hover_color=config.COLORS["danger_hover"],
            text_color="#FFFFFF",
            height=40,
            width=90,
            command=self._confirm_delete
        ).pack(side="left")

        self.edit_save_btn = ctk.CTkButton(
            btn_frame,
            text="Edit Entry",
            fg_color=config.COLORS["primary"],
            hover_color=config.COLORS["primary_hover"],
            font=ctk.CTkFont(size=13, weight="bold"),
            height=40,
            width=120,
            command=self._toggle_edit_save
        )
        self.edit_save_btn.pack(side="right")

    def _set_read_only(self, read_only: bool):
        """Sets entry fields to normal or disabled based on edit state."""
        state = "disabled" if read_only else "normal"
        self.title_entry.configure(state=state)
        self.user_entry.configure(state=state)
        self.pass_entry.configure(state=state)
        self.url_entry.configure(state=state)
        self.category_opt.configure(state=state)
        self.notes_text.configure(state=state)
        if read_only:
            self.gen_btn.pack_forget()
        else:
            self.gen_btn.pack(side="right")

    def _toggle_pass(self):
        self.show_pass = not self.show_pass
        if self.show_pass:
            self.pass_entry.configure(show="")
            self.eye_btn.configure(text="🙈")
        else:
            self.pass_entry.configure(show="•")
            self.eye_btn.configure(text="👁")

    def _on_password_change(self, event=None):
        self._update_strength_display()

    def _update_strength_display(self):
        pwd = self.pass_entry.get()
        res = evaluate_password_strength(pwd)
        self.strength_bar.update_strength(res["score"], res["label"], res["color"])

    def _copy_username(self):
        usr = self.user_entry.get().strip()
        if usr:
            ClipboardManager.copy_with_autoclear(usr, clear_after_seconds=30)
            ToastNotification(self, "Username copied to clipboard!", is_error=False)

    def _copy_password(self):
        pwd = self.pass_entry.get()
        if pwd:
            sec = int(self.auth.db.get_setting("clipboard_clear_seconds", str(config.DEFAULT_CLIPBOARD_CLEAR_SECONDS)))
            ClipboardManager.copy_with_autoclear(pwd, clear_after_seconds=sec)
            msg = f"Password copied! Clipboard clears in {sec}s." if sec > 0 else "Password copied to clipboard!"
            ToastNotification(self, msg, is_error=False)

    def _generate_pass(self):
        pwd = generate_password(length=20, use_uppercase=True, use_lowercase=True, use_numbers=True, use_symbols=True)
        self.pass_entry.configure(state="normal")
        self.pass_entry.delete(0, "end")
        self.pass_entry.insert(0, pwd)
        self.pass_entry.configure(show="")
        self.show_pass = True
        self.eye_btn.configure(text="🙈")
        self._update_strength_display()
        ToastNotification(self, "Generated new strong password!", is_error=False)

    def _open_url(self):
        raw = self.url_entry.get().strip()
        url = sanitize_url(raw)
        if url:
            webbrowser.open(url)

    def _toggle_favorite(self):
        self.entry.favorite = not self.entry.favorite
        star_symbol = "⭐" if self.entry.favorite else "☆"
        self.fav_btn.configure(text=star_symbol)
        if self.entry.id:
            self.auth.db.set_favorite(self.entry.id, self.entry.favorite)
            if self.on_changed_cb:
                self.on_changed_cb()

    def _close_dialog(self):
        try:
            self.grab_release()
        except Exception:
            pass
        self.after(30, self.destroy)

    def _toggle_edit_save(self):
        if not self.is_edit_mode:
            # Enable Edit mode
            self.is_edit_mode = True
            self._set_read_only(False)
            self.edit_save_btn.configure(text="Save Changes", fg_color=config.COLORS["success"])
        else:
            # Save Changes
            title = self.title_entry.get().strip()
            pwd = self.pass_entry.get()
            if not title or not pwd:
                ToastNotification(self, "Title and Password cannot be empty.", is_error=True)
                return

            self.entry.title = title
            self.entry.username = self.user_entry.get().strip()
            self.entry.password = pwd
            self.entry.url = self.url_entry.get().strip()
            self.entry.category = self.category_opt.get()
            self.entry.notes = self.notes_text.get("1.0", "end-1c").strip()

            encrypted_data = self.auth.encrypt_entry(self.entry)
            if self.entry.id:
                self.auth.db.update_entry(self.entry.id, encrypted_data)
                ToastNotification(self.master, f"Saved changes to '{title}'!", is_error=False)
                self._close_dialog()
                if self.on_changed_cb:
                    self.on_changed_cb()

    def _confirm_delete(self):
        ConfirmDialog(
            self,
            title="Delete Password?",
            message=f"Are you sure you want to delete '{self.entry.title}'? This action cannot be undone.",
            on_confirm=self._delete_entry
        )

    def _delete_entry(self):
        if self.entry.id:
            self.auth.db.delete_entry(self.entry.id)
            ToastNotification(self.master, f"Deleted '{self.entry.title}'.", is_error=False)
            self._close_dialog()
            if self.on_changed_cb:
                self.on_changed_cb()
