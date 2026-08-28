"""
VaultX Dedicated Password Generator View.
Provides interactive password generation with sliders, character set toggles, and live strength meter.
"""

import customtkinter as ctk

from app import config
from app.password_generator import generate_password, evaluate_password_strength
from app.utils import ClipboardManager
from ui.components import ModernCard, PasswordStrengthBar, ToastNotification


class PasswordGeneratorView(ctk.CTkFrame):
    """View container for dedicated Password Generator."""

    def __init__(self, master, auth_manager):
        super().__init__(master, fg_color="transparent")
        self.auth = auth_manager
        self.length_val = 20

        self._build_ui()
        self._generate_new_password()

    def _build_ui(self):
        card = ModernCard(self, width=600)
        card.pack(fill="both", expand=True, padx=24, pady=24)

        # Header
        ctk.CTkLabel(
            card,
            text="🔑 Password Generator",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=config.COLORS["text"]
        ).pack(anchor="w", padx=24, pady=(24, 4))

        ctk.CTkLabel(
            card,
            text="Generate cryptographically secure random passwords using Python's secrets module.",
            font=ctk.CTkFont(size=13),
            text_color=config.COLORS["muted"]
        ).pack(anchor="w", padx=24, pady=(0, 20))

        # Output Box Frame
        output_frame = ctk.CTkFrame(card, fg_color=config.COLORS["input_bg"], border_color=config.COLORS["border"], border_width=1, corner_radius=8)
        output_frame.pack(fill="x", padx=24, pady=(0, 16))

        self.password_entry = ctk.CTkEntry(
            output_frame,
            font=ctk.CTkFont(family="Consolas", size=16, weight="bold"),
            fg_color="transparent",
            border_width=0,
            height=48,
            text_color=config.COLORS["text"]
        )
        self.password_entry.pack(side="left", fill="x", expand=True, padx=16)

        ctk.CTkButton(
            output_frame,
            text="📋 Copy",
            width=90,
            height=36,
            fg_color=config.COLORS["primary"],
            hover_color=config.COLORS["primary_hover"],
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._copy_password
        ).pack(side="right", padx=8)

        # Password Strength Bar
        self.strength_bar = PasswordStrengthBar(card)
        self.strength_bar.pack(fill="x", padx=24, pady=(0, 24))

        # Controls Section
        ctk.CTkLabel(
            card,
            text="Length",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=config.COLORS["text"]
        ).pack(anchor="w", padx=24, pady=(0, 4))

        slider_frame = ctk.CTkFrame(card, fg_color="transparent")
        slider_frame.pack(fill="x", padx=24, pady=(0, 20))

        self.slider = ctk.CTkSlider(
            slider_frame,
            from_=8,
            to=64,
            number_of_steps=56,
            command=self._on_slider_change
        )
        self.slider.set(self.length_val)
        self.slider.pack(side="left", fill="x", expand=True, padx=(0, 16))

        self.length_lbl = ctk.CTkLabel(
            slider_frame,
            text=str(self.length_val),
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=config.COLORS["primary"],
            width=36
        )
        self.length_lbl.pack(side="right")

        # Options Checkboxes
        opts_frame = ctk.CTkFrame(card, fg_color="transparent")
        opts_frame.pack(fill="x", padx=24, pady=(0, 24))

        self.upper_var = ctk.BooleanVar(value=True)
        self.lower_var = ctk.BooleanVar(value=True)
        self.numbers_var = ctk.BooleanVar(value=True)
        self.symbols_var = ctk.BooleanVar(value=True)
        self.ambiguous_var = ctk.BooleanVar(value=False)

        ctk.CTkCheckBox(opts_frame, text="Uppercase (A–Z)", variable=self.upper_var, command=self._generate_new_password, fg_color=config.COLORS["primary"]).grid(row=0, column=0, sticky="w", padx=8, pady=8)
        ctk.CTkCheckBox(opts_frame, text="Lowercase (a–z)", variable=self.lower_var, command=self._generate_new_password, fg_color=config.COLORS["primary"]).grid(row=0, column=1, sticky="w", padx=8, pady=8)
        ctk.CTkCheckBox(opts_frame, text="Numbers (0–9)", variable=self.numbers_var, command=self._generate_new_password, fg_color=config.COLORS["primary"]).grid(row=1, column=0, sticky="w", padx=8, pady=8)
        ctk.CTkCheckBox(opts_frame, text="Symbols (!@#$)", variable=self.symbols_var, command=self._generate_new_password, fg_color=config.COLORS["primary"]).grid(row=1, column=1, sticky="w", padx=8, pady=8)
        ctk.CTkCheckBox(opts_frame, text="Exclude ambiguous characters (1, l, I, 0, O)", variable=self.ambiguous_var, command=self._generate_new_password, fg_color=config.COLORS["primary"]).grid(row=2, column=0, columnspan=2, sticky="w", padx=8, pady=8)

        # Generate Button
        ctk.CTkButton(
            card,
            text="🔄 Generate New Password",
            height=44,
            fg_color=config.COLORS["primary"],
            hover_color=config.COLORS["primary_hover"],
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._generate_new_password
        ).pack(fill="x", padx=24, pady=(8, 24))

    def _on_slider_change(self, value):
        self.length_val = int(value)
        self.length_lbl.configure(text=str(self.length_val))
        self._generate_new_password()

    def _generate_new_password(self):
        try:
            pwd = generate_password(
                length=self.length_val,
                use_uppercase=self.upper_var.get(),
                use_lowercase=self.lower_var.get(),
                use_numbers=self.numbers_var.get(),
                use_symbols=self.symbols_var.get(),
                exclude_ambiguous=self.ambiguous_var.get()
            )
            self.password_entry.delete(0, "end")
            self.password_entry.insert(0, pwd)

            res = evaluate_password_strength(pwd)
            self.strength_bar.update_strength(res["score"], res["label"], res["color"])
        except ValueError as e:
            ToastNotification(self.winfo_toplevel(), str(e), is_error=True)

    def _copy_password(self):
        pwd = self.password_entry.get()
        if pwd:
            sec = int(self.auth.db.get_setting("clipboard_clear_seconds", str(config.DEFAULT_CLIPBOARD_CLEAR_SECONDS)))
            ClipboardManager.copy_with_autoclear(pwd, clear_after_seconds=sec)
            msg = f"Password copied! Clipboard clears in {sec}s." if sec > 0 else "Password copied!"
            ToastNotification(self.winfo_toplevel(), msg, is_error=False)
