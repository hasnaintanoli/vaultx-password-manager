"""
VaultX Reusable Modern UI Components.
Includes styled cards, badges, strength progress bars, toast notifications, and modal dialogs.
"""

import customtkinter as ctk
from typing import Optional, Callable
from app import config


class ModernCard(ctk.CTkFrame):
    """Sleek elevated card container with rounded corners and border."""
    def __init__(self, master, fg_color=None, border_color=None, border_width=1, corner_radius=10, **kwargs):
        super().__init__(
            master,
            fg_color=fg_color or config.COLORS["card_bg"],
            border_color=border_color or config.COLORS["border"],
            border_width=border_width,
            corner_radius=corner_radius,
            **kwargs
        )


class CategoryBadge(ctk.CTkFrame):
    """Pill-style badge for categories and statuses."""
    def __init__(self, master, text: str, bg_color: Optional[str] = None, text_color: Optional[str] = None, **kwargs):
        bg = bg_color or config.COLORS["accent_bg"]
        txt = text_color or config.COLORS["text"]
        super().__init__(
            master,
            fg_color=bg,
            corner_radius=12,
            border_width=0,
            **kwargs
        )
        self.label = ctk.CTkLabel(
            self,
            text=text,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=txt,
            padx=10,
            pady=2
        )
        self.label.pack()


class PasswordStrengthBar(ctk.CTkFrame):
    """Animated visual password strength progress bar and label."""
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.progress = ctk.CTkProgressBar(
            self,
            height=8,
            corner_radius=4,
            progress_color=config.COLORS["danger"],
            fg_color=config.COLORS["accent_bg"]
        )
        self.progress.pack(fill="x", expand=True, side="top", pady=(0, 4))
        self.progress.set(0)

        self.label = ctk.CTkLabel(
            self,
            text="Password Strength: N/A",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=config.COLORS["muted"]
        )
        self.label.pack(side="left")

    def update_strength(self, score: int, label_text: str, color: str):
        """Updates bar percentage, label text, and progress bar color."""
        fraction = max(0.05, min(1.0, score / 100.0))
        self.progress.set(fraction)
        self.progress.configure(progress_color=color)
        self.label.configure(
            text=f"Strength: {label_text} ({score}%)",
            text_color=color
        )


class ToastNotification(ctk.CTkToplevel):
    """Floating toast notification popup for user feedback (e.g. Copied to Clipboard)."""
    def __init__(self, master, message: str, is_error: bool = False, duration_ms: int = 2500):
        super().__init__(master)
        self.withdraw()
        self.overrideredirect(True)
        self.attributes("-topmost", True)

        bg_col = config.COLORS["danger"] if is_error else config.COLORS["primary"]
        frame = ctk.CTkFrame(
            self,
            fg_color=bg_col,
            corner_radius=8,
            border_width=1,
            border_color=config.COLORS["border"]
        )
        frame.pack(fill="both", expand=True, padx=2, pady=2)

        lbl = ctk.CTkLabel(
            frame,
            text=message,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#FFFFFF",
            padx=16,
            pady=10
        )
        lbl.pack()

        self.update_idletasks()
        # Position toast near bottom center of master window
        try:
            m_x = master.winfo_rootx()
            m_y = master.winfo_rooty()
            m_w = master.winfo_width()
            m_h = master.winfo_height()

            w = self.winfo_width()
            h = self.winfo_height()

            pos_x = m_x + (m_w // 2) - (w // 2)
            pos_y = m_y + m_h - h - 40
            self.geometry(f"+{pos_x}+{pos_y}")
        except Exception:
            pass

        self.deiconify()
        self.after(duration_ms, self.destroy)


class ConfirmDialog(ctk.CTkToplevel):
    """Confirmation modal dialog for destructive actions."""
    def __init__(self, master, title: str, message: str, on_confirm: Callable[[], None]):
        super().__init__(master)
        self.title(title)
        self.geometry("400x200")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.grab_set()

        self.configure(fg_color=config.COLORS["bg"])
        self.on_confirm = on_confirm

        card = ModernCard(self)
        card.pack(fill="both", expand=True, padx=16, pady=16)

        ctk.CTkLabel(
            card,
            text=title,
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=config.COLORS["danger"]
        ).pack(anchor="w", padx=16, pady=(16, 8))

        ctk.CTkLabel(
            card,
            text=message,
            font=ctk.CTkFont(size=13),
            text_color=config.COLORS["text"],
            wraplength=340,
            justify="left"
        ).pack(anchor="w", padx=16, pady=(0, 16))

        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(fill="x", side="bottom", padx=16, pady=16)

        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            fg_color=config.COLORS["accent_bg"],
            hover_color=config.COLORS["surface_hover"],
            text_color=config.COLORS["text"],
            width=100,
            command=self._close_dialog
        ).pack(side="left")

        ctk.CTkButton(
            btn_frame,
            text="Delete",
            fg_color=config.COLORS["danger"],
            hover_color=config.COLORS["danger_hover"],
            text_color="#FFFFFF",
            width=100,
            command=self._confirm_click
        ).pack(side="right")

    def _close_dialog(self):
        try:
            self.grab_release()
        except Exception:
            pass
        self.after(30, self.destroy)

    def _confirm_click(self):
        self._close_dialog()
        if self.on_confirm:
            self.after(40, self.on_confirm)
