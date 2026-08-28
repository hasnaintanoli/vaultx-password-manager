"""
VaultX Login & First-Launch Setup Window.
Displays either the setup screen for new vaults or the unlock screen for existing vaults.
"""

import customtkinter as ctk
from typing import Callable, Optional
from PIL import Image

from app import config
from app.auth import AuthManager
from app.password_generator import evaluate_password_strength
from ui.components import ModernCard, PasswordStrengthBar, ToastNotification


class LoginWindow(ctk.CTkFrame):
    """Container frame for VaultX authentication (Setup or Login)."""

    def __init__(self, master, auth_manager: AuthManager, on_login_success: Callable[[], None]):
        super().__init__(master, fg_color=config.COLORS["bg"])
        self.auth = auth_manager
        self.on_login_success = on_login_success
        self.show_pass_var = False

        self._build_ui()

    def _build_ui(self):
        """Constructs either setup screen or login screen based on vault state."""
        # Clear existing children
        for child in self.winfo_children():
            child.destroy()

        # Center card container
        self.center_container = ctk.CTkFrame(self, fg_color="transparent")
        self.center_container.place(relx=0.5, rely=0.5, anchor="center")

        # Logo and Title Header
        if config.ICON_PNG_PATH.exists():
            try:
                pil_icon = Image.open(config.ICON_PNG_PATH)
                self.app_logo_img = ctk.CTkImage(light_image=pil_icon, dark_image=pil_icon, size=(60, 60))
                icon_lbl = ctk.CTkLabel(self.center_container, image=self.app_logo_img, text="")
                icon_lbl.pack(pady=(0, 8))
            except Exception:
                pass

        logo_label = ctk.CTkLabel(
            self.center_container,
            text="VaultX",
            font=ctk.CTkFont(size=34, weight="bold"),
            text_color=config.COLORS["text"]
        )
        logo_label.pack(pady=(0, 4))

        tagline_label = ctk.CTkLabel(
            self.center_container,
            text=config.APP_TAGLINE,
            font=ctk.CTkFont(size=14),
            text_color=config.COLORS["muted"]
        )
        tagline_label.pack(pady=(0, 20))

        if not self.auth.is_vault_created():
            self._render_setup_form()
        else:
            self._render_login_form()

    def _render_setup_form(self):
        """Renders first launch setup form to create a new vault master password."""
        card = ModernCard(self.center_container, width=420)
        card.pack(padx=20, pady=10, fill="both", expand=True)

        ctk.CTkLabel(
            card,
            text="Create Your Master Password",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=config.COLORS["text"]
        ).pack(anchor="w", padx=24, pady=(24, 8))

        ctk.CTkLabel(
            card,
            text=f"The master password protects your vault. Choose a strong password of at least {config.MIN_MASTER_PASSWORD_LENGTH} characters.",
            font=ctk.CTkFont(size=12),
            text_color=config.COLORS["muted"],
            wraplength=360,
            justify="left"
        ).pack(anchor="w", padx=24, pady=(0, 16))

        # Master Password Input
        ctk.CTkLabel(
            card,
            text="Master Password",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=config.COLORS["text"]
        ).pack(anchor="w", padx=24, pady=(4, 2))

        self.pass_entry = ctk.CTkEntry(
            card,
            show="•",
            placeholder_text="Enter master password...",
            height=40,
            fg_color=config.COLORS["input_bg"],
            border_color=config.COLORS["border"]
        )
        self.pass_entry.pack(fill="x", padx=24, pady=(0, 12))
        self.pass_entry.bind("<KeyRelease>", self._on_password_key_release)

        # Confirm Password Input
        ctk.CTkLabel(
            card,
            text="Confirm Master Password",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=config.COLORS["text"]
        ).pack(anchor="w", padx=24, pady=(4, 2))

        self.confirm_entry = ctk.CTkEntry(
            card,
            show="•",
            placeholder_text="Confirm master password...",
            height=40,
            fg_color=config.COLORS["input_bg"],
            border_color=config.COLORS["border"]
        )
        self.confirm_entry.pack(fill="x", padx=24, pady=(0, 16))
        self.confirm_entry.bind("<Return>", lambda e: self._create_vault())

        # Password Strength Bar Component
        self.strength_bar = PasswordStrengthBar(card)
        self.strength_bar.pack(fill="x", padx=24, pady=(0, 16))

        # Error label
        self.error_label = ctk.CTkLabel(
            card,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=config.COLORS["danger"],
            wraplength=360
        )
        self.error_label.pack(anchor="w", padx=24, pady=(0, 8))

        # Submit Button
        self.create_btn = ctk.CTkButton(
            card,
            text="Create Vault",
            height=42,
            fg_color=config.COLORS["primary"],
            hover_color=config.COLORS["primary_hover"],
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._create_vault
        )
        self.create_btn.pack(fill="x", padx=24, pady=(8, 24))

    def _render_login_form(self):
        """Renders standard unlock form for existing vaults."""
        card = ModernCard(self.center_container, width=400)
        card.pack(padx=20, pady=10, fill="both", expand=True)

        ctk.CTkLabel(
            card,
            text="Welcome Back",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=config.COLORS["text"]
        ).pack(anchor="w", padx=24, pady=(24, 4))

        ctk.CTkLabel(
            card,
            text="Enter your master password to unlock your vault.",
            font=ctk.CTkFont(size=13),
            text_color=config.COLORS["muted"]
        ).pack(anchor="w", padx=24, pady=(0, 20))

        # Password Input Frame (Entry + Toggle eye button)
        ctk.CTkLabel(
            card,
            text="Master Password",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=config.COLORS["text"]
        ).pack(anchor="w", padx=24, pady=(4, 2))

        pass_frame = ctk.CTkFrame(card, fg_color="transparent")
        pass_frame.pack(fill="x", padx=24, pady=(0, 16))

        self.login_pass_entry = ctk.CTkEntry(
            pass_frame,
            show="•",
            placeholder_text="Enter master password...",
            height=42,
            fg_color=config.COLORS["input_bg"],
            border_color=config.COLORS["border"]
        )
        self.login_pass_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.login_pass_entry.bind("<Return>", lambda e: self._unlock_vault())
        # Defer focus to avoid TclError during screen transition
        self.after(100, lambda: self.login_pass_entry.focus_set() if self.login_pass_entry.winfo_exists() else None)

        self.toggle_btn = ctk.CTkButton(
            pass_frame,
            text="👁",
            width=42,
            height=42,
            fg_color=config.COLORS["accent_bg"],
            hover_color=config.COLORS["surface_hover"],
            command=self._toggle_password_visibility
        )
        self.toggle_btn.pack(side="right")

        # Error / Status Label
        self.login_error_label = ctk.CTkLabel(
            card,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=config.COLORS["danger"],
            wraplength=340
        )
        self.login_error_label.pack(anchor="w", padx=24, pady=(0, 8))

        # Attempts counter
        self.attempts_label = ctk.CTkLabel(
            card,
            text="Incorrect password attempts: 0",
            font=ctk.CTkFont(size=12),
            text_color=config.COLORS["muted"]
        )
        self.attempts_label.pack(anchor="w", padx=24, pady=(0, 16))

        # Unlock Button
        self.unlock_btn = ctk.CTkButton(
            card,
            text="Unlock Vault",
            height=44,
            fg_color=config.COLORS["primary"],
            hover_color=config.COLORS["primary_hover"],
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._unlock_vault
        )
        self.unlock_btn.pack(fill="x", padx=24, pady=(8, 24))

    def _on_password_key_release(self, event=None):
        """Calculates live password strength on setup screen."""
        pwd = self.pass_entry.get()
        if not pwd:
            self.strength_bar.update_strength(0, "N/A", config.COLORS["muted"])
            return

        res = evaluate_password_strength(pwd)
        self.strength_bar.update_strength(res["score"], res["label"], res["color"])

    def _toggle_password_visibility(self):
        """Toggles show/hide password in entry field."""
        self.show_pass_var = not self.show_pass_var
        if self.show_pass_var:
            self.login_pass_entry.configure(show="")
            self.toggle_btn.configure(text="🙈")
        else:
            self.login_pass_entry.configure(show="•")
            self.toggle_btn.configure(text="👁")

    def _create_vault(self):
        """Handles vault setup form submission."""
        pwd = self.pass_entry.get()
        confirm = self.confirm_entry.get()

        if not pwd:
            self.error_label.configure(text="Please enter a master password.")
            return

        if len(pwd) < config.MIN_MASTER_PASSWORD_LENGTH:
            self.error_label.configure(
                text=f"Master password must be at least {config.MIN_MASTER_PASSWORD_LENGTH} characters long."
            )
            return

        if pwd != confirm:
            self.error_label.configure(text="Passwords do not match. Please re-enter.")
            return

        self.error_label.configure(text="")
        success, msg = self.auth.create_vault(pwd)
        if success:
            ToastNotification(self.winfo_toplevel(), "Vault created successfully!", is_error=False)
            self.on_login_success()
        else:
            self.error_label.configure(text=msg)

    def _unlock_vault(self):
        """Handles login unlock submission."""
        pwd = self.login_pass_entry.get()
        if not pwd:
            self.login_error_label.configure(text="Please enter your master password.")
            return

        success, msg = self.auth.unlock_vault(pwd)
        if success:
            self.login_pass_entry.delete(0, "end")
            self.login_error_label.configure(text="")
            self.on_login_success()
        else:
            self.login_pass_entry.delete(0, "end")
            self.login_error_label.configure(text=msg)
            self.attempts_label.configure(
                text=f"Incorrect password attempts: {self.auth.incorrect_attempts}"
            )
