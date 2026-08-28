"""
VaultX Dashboard Vault Items & Health View.
Displays statistics banner, category filtering, search results, item cards, and quick actions.
"""

import customtkinter as ctk
from typing import Callable, List, Optional

from app import config
from app.auth import AuthManager
from app.models import VaultEntry, VaultHealthStats
from app.password_generator import evaluate_password_strength
from app.utils import ClipboardManager
from ui.add_entry import AddEntryDialog
from ui.components import ModernCard, CategoryBadge, ToastNotification
from ui.edit_entry import EditEntryDialog


class VaultView(ctk.CTkFrame):
    """View container for vault items list, filters, and health dashboard."""

    def __init__(self, master, auth_manager: AuthManager, on_vault_updated_cb: Optional[Callable[[], None]] = None):
        super().__init__(master, fg_color="transparent")
        self.auth = auth_manager
        self.on_vault_updated_cb = on_vault_updated_cb

        self.current_filter_category: Optional[str] = None
        self.favorites_only: bool = False
        self.search_query: str = ""
        self.all_entries: List[VaultEntry] = []

        self._build_ui()
        self.refresh_vault()

    def _build_ui(self):
        # Top Dashboard Health Stats Banner
        self.stats_container = ctk.CTkFrame(self, fg_color="transparent")
        self.stats_container.pack(fill="x", padx=24, pady=(20, 10))

        # Main List Scrollable Area
        self.list_scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.list_scroll.pack(fill="both", expand=True, padx=24, pady=(0, 20))

    def refresh_vault(self):
        """Fetches and decrypts all entries from database and updates UI."""
        if not self.auth.is_unlocked():
            return

        self.all_entries = self.auth.decrypt_all_entries()
        self._render_stats_banner()
        self._render_items_list()

    def set_filter(self, category: Optional[str] = None, favorites_only: bool = False, search_query: str = ""):
        """Sets filter parameters and refreshes view."""
        self.current_filter_category = category
        self.favorites_only = favorites_only
        self.search_query = search_query.strip().lower()
        self._render_items_list()

    def _calculate_health_stats(self) -> VaultHealthStats:
        """Calculates health metrics across all entries."""
        stats = VaultHealthStats()
        stats.total_items = len(self.all_entries)

        for entry in self.all_entries:
            if entry.favorite:
                stats.favorites_count += 1

            eval_res = evaluate_password_strength(entry.password)
            score = eval_res["score"]
            if score < 40:
                stats.weak_count += 1
            elif score < 70:
                stats.medium_count += 1
            else:
                stats.strong_count += 1

        return stats

    def _render_stats_banner(self):
        """Renders non-sensitive dashboard health statistics cards."""
        for child in self.stats_container.winfo_children():
            child.destroy()

        stats = self._calculate_health_stats()

        # Grid of Stat Cards
        grid = ctk.CTkFrame(self.stats_container, fg_color="transparent")
        grid.pack(fill="x")

        # Card 1: Total Items
        c1 = ModernCard(grid)
        c1.pack(side="left", fill="both", expand=True, padx=(0, 8))
        ctk.CTkLabel(c1, text="Total Items", font=ctk.CTkFont(size=12), text_color=config.COLORS["muted"]).pack(anchor="w", padx=16, pady=(12, 2))
        ctk.CTkLabel(c1, text=str(stats.total_items), font=ctk.CTkFont(size=22, weight="bold"), text_color=config.COLORS["text"]).pack(anchor="w", padx=16, pady=(0, 12))

        # Card 2: Favorites
        c2 = ModernCard(grid)
        c2.pack(side="left", fill="both", expand=True, padx=(0, 8))
        ctk.CTkLabel(c2, text="Favorites ⭐", font=ctk.CTkFont(size=12), text_color=config.COLORS["muted"]).pack(anchor="w", padx=16, pady=(12, 2))
        ctk.CTkLabel(c2, text=str(stats.favorites_count), font=ctk.CTkFont(size=22, weight="bold"), text_color=config.COLORS["warning"]).pack(anchor="w", padx=16, pady=(0, 12))

        # Card 3: Strong Passwords
        c3 = ModernCard(grid)
        c3.pack(side="left", fill="both", expand=True, padx=(0, 8))
        ctk.CTkLabel(c3, text="Strong Passwords", font=ctk.CTkFont(size=12), text_color=config.COLORS["muted"]).pack(anchor="w", padx=16, pady=(12, 2))
        ctk.CTkLabel(c3, text=str(stats.strong_count), font=ctk.CTkFont(size=22, weight="bold"), text_color=config.COLORS["success"]).pack(anchor="w", padx=16, pady=(0, 12))

        # Card 4: Weak Passwords
        c4 = ModernCard(grid)
        c4.pack(side="left", fill="both", expand=True)
        ctk.CTkLabel(c4, text="Weak Passwords", font=ctk.CTkFont(size=12), text_color=config.COLORS["muted"]).pack(anchor="w", padx=16, pady=(12, 2))
        ctk.CTkLabel(c4, text=str(stats.weak_count), font=ctk.CTkFont(size=22, weight="bold"), text_color=config.COLORS["danger"]).pack(anchor="w", padx=16, pady=(0, 12))

        # Health Banner if weak passwords exist
        if stats.weak_count > 0:
            health_card = ModernCard(self.stats_container, fg_color="#1E1417", border_color=config.COLORS["danger"])
            health_card.pack(fill="x", pady=(10, 0))

            lbl = ctk.CTkLabel(
                health_card,
                text=f"⚠️ Password Health: {stats.weak_count} password(s) need attention! Update them for maximum security.",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=config.COLORS["danger"]
            )
            lbl.pack(anchor="w", padx=16, pady=10)

    def _render_items_list(self):
        """Renders entry cards filtered by search and categories."""
        for child in self.list_scroll.winfo_children():
            child.destroy()

        # Apply filtering
        filtered = []
        for entry in self.all_entries:
            if self.favorites_only and not entry.favorite:
                continue
            if self.current_filter_category and entry.category != self.current_filter_category:
                continue
            if self.search_query:
                match_title = self.search_query in entry.title.lower()
                match_user = self.search_query in entry.username.lower()
                match_url = self.search_query in entry.url.lower()
                match_cat = self.search_query in entry.category.lower()
                if not (match_title or match_user or match_url or match_cat):
                    continue
            filtered.append(entry)

        if not filtered:
            empty_card = ModernCard(self.list_scroll)
            empty_card.pack(fill="x", pady=20)
            msg = "No vault items match your search or filter." if self.all_entries else "Your vault is empty. Click '+ Add Item' to store your first password!"
            ctk.CTkLabel(
                empty_card,
                text=msg,
                font=ctk.CTkFont(size=14),
                text_color=config.COLORS["muted"]
            ).pack(padx=20, pady=30)
            return

        # Render item cards
        for entry in filtered:
            self._create_entry_item_card(entry)

    def _create_entry_item_card(self, entry: VaultEntry):
        card = ModernCard(self.list_scroll)
        card.pack(fill="x", pady=6)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=12)

        # Icon / Badge column
        icon_lbl = ctk.CTkLabel(inner, text="🔑", font=ctk.CTkFont(size=20))
        icon_lbl.pack(side="left", padx=(0, 12))

        # Title and Username Info
        info_frame = ctk.CTkFrame(inner, fg_color="transparent")
        info_frame.pack(side="left", fill="x", expand=True)

        title_row = ctk.CTkFrame(info_frame, fg_color="transparent")
        title_row.pack(anchor="w")

        title_btn = ctk.CTkButton(
            title_row,
            text=entry.title,
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=config.COLORS["text"],
            fg_color="transparent",
            hover=False,
            anchor="w",
            command=lambda e=entry: self._open_edit_dialog(e)
        )
        title_btn.pack(side="left", padx=(0, 8))

        if entry.favorite:
            ctk.CTkLabel(title_row, text="⭐", font=ctk.CTkFont(size=12)).pack(side="left", padx=(0, 6))

        CategoryBadge(title_row, text=entry.category).pack(side="left")

        user_text = entry.username or "(No username specified)"
        ctk.CTkLabel(
            info_frame,
            text=user_text,
            font=ctk.CTkFont(size=12),
            text_color=config.COLORS["muted"]
        ).pack(anchor="w")

        # Action Buttons (Copy Password, View Details)
        btn_frame = ctk.CTkFrame(inner, fg_color="transparent")
        btn_frame.pack(side="right")

        ctk.CTkButton(
            btn_frame,
            text="📋 Copy Pass",
            width=96,
            height=34,
            fg_color=config.COLORS["accent_bg"],
            hover_color=config.COLORS["surface_hover"],
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda e=entry: self._copy_entry_password(e)
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_frame,
            text="View 👁",
            width=70,
            height=34,
            fg_color=config.COLORS["primary"],
            hover_color=config.COLORS["primary_hover"],
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda e=entry: self._open_edit_dialog(e)
        ).pack(side="left")

    def _copy_entry_password(self, entry: VaultEntry):
        if entry.password:
            sec = int(self.auth.db.get_setting("clipboard_clear_seconds", str(config.DEFAULT_CLIPBOARD_CLEAR_SECONDS)))
            ClipboardManager.copy_with_autoclear(entry.password, clear_after_seconds=sec)
            msg = f"Copied password for '{entry.title}'! Clipboard clears in {sec}s." if sec > 0 else f"Copied password for '{entry.title}'!"
            ToastNotification(self.winfo_toplevel(), msg, is_error=False)

    def _open_edit_dialog(self, entry: VaultEntry):
        EditEntryDialog(self.winfo_toplevel(), self.auth, entry, on_changed_cb=self._on_vault_changed)

    def open_add_dialog(self):
        AddEntryDialog(self.winfo_toplevel(), self.auth, on_saved_cb=self._on_vault_changed)

    def _on_vault_changed(self):
        self.refresh_vault()
        if self.on_vault_updated_cb:
            self.on_vault_updated_cb()
