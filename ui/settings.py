"""
VaultX Settings View.
Provides security configurations, auto-lock timeouts, clipboard settings, and encrypted backup/restore.
"""

from pathlib import Path
from tkinter import filedialog, simpledialog
import customtkinter as ctk

from app import config
from app.auth import AuthManager
from app.crypto import create_encrypted_backup, restore_encrypted_backup
from ui.components import ModernCard, ToastNotification, ConfirmDialog


class SettingsView(ctk.CTkFrame):
    """View container for VaultX Settings & Preferences."""

    def __init__(self, master, auth_manager: AuthManager, on_settings_changed_cb=None):
        super().__init__(master, fg_color="transparent")
        self.auth = auth_manager
        self.on_settings_changed_cb = on_settings_changed_cb

        self._build_ui()

    def _build_ui(self):
        scrollable = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scrollable.pack(fill="both", expand=True, padx=24, pady=24)

        # Header
        ctk.CTkLabel(
            scrollable,
            text="⚙ Settings & Security Preferences",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=config.COLORS["text"]
        ).pack(anchor="w", pady=(0, 4))

        ctk.CTkLabel(
            scrollable,
            text="Manage auto-lock timers, clipboard behavior, theme options, and encrypted backups.",
            font=ctk.CTkFont(size=13),
            text_color=config.COLORS["muted"]
        ).pack(anchor="w", pady=(0, 20))

        # --- Section 1: Security Preferences ---
        sec_card = ModernCard(scrollable)
        sec_card.pack(fill="x", pady=(0, 16))

        ctk.CTkLabel(sec_card, text="Security & Timeouts", font=ctk.CTkFont(size=16, weight="bold"), text_color=config.COLORS["text"]).pack(anchor="w", padx=20, pady=(20, 12))

        # Auto Lock Option
        ctk.CTkLabel(sec_card, text="Auto-lock Timeout", font=ctk.CTkFont(size=13, weight="bold"), text_color=config.COLORS["text"]).pack(anchor="w", padx=20, pady=(4, 2))
        
        current_autolock = self.auth.db.get_setting("auto_lock_minutes", str(config.DEFAULT_AUTO_LOCK_MINUTES))
        autolock_label_val = [k for k, v in config.AUTO_LOCK_OPTIONS.items() if str(v) == current_autolock]
        init_autolock = autolock_label_val[0] if autolock_label_val else "5 minutes"

        self.autolock_opt = ctk.CTkOptionMenu(
            sec_card,
            values=list(config.AUTO_LOCK_OPTIONS.keys()),
            height=38,
            fg_color=config.COLORS["input_bg"],
            button_color=config.COLORS["accent_bg"],
            command=self._on_autolock_change
        )
        self.autolock_opt.set(init_autolock)
        self.autolock_opt.pack(anchor="w", padx=20, pady=(0, 16))

        # Clipboard Clear Option
        ctk.CTkLabel(sec_card, text="Clipboard Auto-clear Timeout", font=ctk.CTkFont(size=13, weight="bold"), text_color=config.COLORS["text"]).pack(anchor="w", padx=20, pady=(4, 2))

        current_clip = self.auth.db.get_setting("clipboard_clear_seconds", str(config.DEFAULT_CLIPBOARD_CLEAR_SECONDS))
        clip_label_val = [k for k, v in config.CLIPBOARD_OPTIONS.items() if str(v) == current_clip]
        init_clip = clip_label_val[0] if clip_label_val else "30 seconds"

        self.clip_opt = ctk.CTkOptionMenu(
            sec_card,
            values=list(config.CLIPBOARD_OPTIONS.keys()),
            height=38,
            fg_color=config.COLORS["input_bg"],
            button_color=config.COLORS["accent_bg"],
            command=self._on_clipboard_change
        )
        self.clip_opt.set(init_clip)
        self.clip_opt.pack(anchor="w", padx=20, pady=(0, 20))

        # --- Section 2: Appearance & Theme ---
        app_card = ModernCard(scrollable)
        app_card.pack(fill="x", pady=(0, 16))

        ctk.CTkLabel(app_card, text="Appearance", font=ctk.CTkFont(size=16, weight="bold"), text_color=config.COLORS["text"]).pack(anchor="w", padx=20, pady=(20, 12))

        ctk.CTkLabel(app_card, text="Application Theme", font=ctk.CTkFont(size=13, weight="bold"), text_color=config.COLORS["text"]).pack(anchor="w", padx=20, pady=(4, 2))
        
        current_theme = self.auth.db.get_setting("theme", "Dark")
        self.theme_opt = ctk.CTkOptionMenu(
            app_card,
            values=["Dark", "Light"],
            height=38,
            fg_color=config.COLORS["input_bg"],
            button_color=config.COLORS["accent_bg"],
            command=self._on_theme_change
        )
        self.theme_opt.set(current_theme)
        self.theme_opt.pack(anchor="w", padx=20, pady=(0, 20))

        # --- Section 3: Vault Backup & Restore ---
        bk_card = ModernCard(scrollable)
        bk_card.pack(fill="x", pady=(0, 16))

        ctk.CTkLabel(bk_card, text="Encrypted Backup & Restore", font=ctk.CTkFont(size=16, weight="bold"), text_color=config.COLORS["text"]).pack(anchor="w", padx=20, pady=(20, 6))

        ctk.CTkLabel(
            bk_card,
            text="Create an encrypted .vaultx backup file or restore an existing backup. Backups are protected using Argon2id encryption.",
            font=ctk.CTkFont(size=12),
            text_color=config.COLORS["muted"],
            wraplength=520,
            justify="left"
        ).pack(anchor="w", padx=20, pady=(0, 16))

        bk_btn_frame = ctk.CTkFrame(bk_card, fg_color="transparent")
        bk_btn_frame.pack(fill="x", padx=20, pady=(0, 20))

        ctk.CTkButton(
            bk_btn_frame,
            text="📦 Create Encrypted Backup",
            height=40,
            fg_color=config.COLORS["primary"],
            hover_color=config.COLORS["primary_hover"],
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._create_backup
        ).pack(side="left", padx=(0, 12))

        ctk.CTkButton(
            bk_btn_frame,
            text="📥 Restore Encrypted Backup",
            height=40,
            fg_color=config.COLORS["accent_bg"],
            hover_color=config.COLORS["surface_hover"],
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._restore_backup
        ).pack(side="left")

    def _on_autolock_change(self, choice):
        minutes = config.AUTO_LOCK_OPTIONS.get(choice, 5)
        self.auth.db.set_setting("auto_lock_minutes", str(minutes))
        ToastNotification(self.winfo_toplevel(), f"Auto-lock set to {choice}.", is_error=False)
        if self.on_settings_changed_cb:
            self.on_settings_changed_cb()

    def _on_clipboard_change(self, choice):
        seconds = config.CLIPBOARD_OPTIONS.get(choice, 30)
        self.auth.db.set_setting("clipboard_clear_seconds", str(seconds))
        ToastNotification(self.winfo_toplevel(), f"Clipboard clear set to {choice}.", is_error=False)

    def _on_theme_change(self, choice):
        self.auth.db.set_setting("theme", choice)
        ctk.set_appearance_mode(choice.lower())
        ToastNotification(self.winfo_toplevel(), f"Theme changed to {choice}.", is_error=False)

    def _create_backup(self):
        if not self.auth.is_unlocked():
            ToastNotification(self.winfo_toplevel(), "Vault must be unlocked to create backup.", is_error=True)
            return

        entries = self.auth.db.get_all_entries()
        if not entries:
            ToastNotification(self.winfo_toplevel(), "Vault is empty. Nothing to backup.", is_error=True)
            return

        # Prompt for backup password
        pass_dialog = ctk.CTkInputDialog(
            text="Enter a password to encrypt this backup file:\n(Minimum 8 characters)",
            title="Backup Password - VaultX"
        )
        backup_pwd = pass_dialog.get_input()

        if not backup_pwd or len(backup_pwd) < 8:
            ToastNotification(self.winfo_toplevel(), "Backup password must be at least 8 characters.", is_error=True)
            return

        target_file = filedialog.asksaveasfilename(
            title="Save Encrypted Vault Backup",
            defaultextension=".vaultx",
            filetypes=[("VaultX Backup Files", "*.vaultx"), ("All Files", "*.*")],
            initialdir=config.EXPORTS_DIR
        )

        if not target_file:
            return

        try:
            backup_content = create_encrypted_backup(entries, backup_pwd)
            with open(target_file, "w", encoding="utf-8") as f:
                f.write(backup_content)
            ToastNotification(self.winfo_toplevel(), f"Encrypted backup saved to {Path(target_file).name}!", is_error=False)
        except Exception as e:
            ToastNotification(self.winfo_toplevel(), f"Failed to create backup: {e}", is_error=True)

    def _restore_backup(self):
        if not self.auth.is_unlocked():
            ToastNotification(self.winfo_toplevel(), "Vault must be unlocked to restore backup.", is_error=True)
            return

        backup_path = filedialog.askopenfilename(
            title="Select Encrypted VaultX Backup File",
            filetypes=[("VaultX Backup Files", "*.vaultx"), ("All Files", "*.*")],
            initialdir=config.EXPORTS_DIR
        )

        if not backup_path:
            return

        pass_dialog = ctk.CTkInputDialog(
            text="Enter the password used to encrypt this backup file:",
            title="Unlock Backup - VaultX"
        )
        backup_pwd = pass_dialog.get_input()

        if not backup_pwd:
            return

        try:
            with open(backup_path, "r", encoding="utf-8") as f:
                backup_str = f.read()

            restored_entries = restore_encrypted_backup(backup_str, backup_pwd)

            def do_replace():
                self.auth.db.replace_all_entries(restored_entries)
                ToastNotification(self.winfo_toplevel(), f"Successfully restored {len(restored_entries)} items!", is_error=False)
                if self.on_settings_changed_cb:
                    self.on_settings_changed_cb()

            ConfirmDialog(
                self,
                title="Restore Backup?",
                message=f"Restoring will overwrite current vault entries with {len(restored_entries)} items from the backup. Continue?",
                on_confirm=do_replace
            )
        except ValueError as ve:
            ToastNotification(self.winfo_toplevel(), str(ve), is_error=True)
        except Exception as e:
            ToastNotification(self.winfo_toplevel(), f"Restore error: {e}", is_error=True)
