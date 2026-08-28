"""
VaultX Data Models.
Defines VaultEntry and VaultHealthStats structures used across the application.
"""

from dataclasses import dataclass, asdict, field
from typing import Optional, Dict, Any
from app.utils import format_iso_datetime


@dataclass
class VaultEntry:
    """Represents a password/secure note item in the vault."""
    id: Optional[int] = None
    title: str = ""
    username: str = ""
    password: str = ""
    url: str = ""
    notes: str = ""
    category: str = "Other"
    favorite: bool = False
    created_at: str = field(default_factory=format_iso_datetime)
    updated_at: str = field(default_factory=format_iso_datetime)

    def to_dict(self) -> Dict[str, Any]:
        """Converts model to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VaultEntry":
        """Creates model from dictionary, safely parsing fields."""
        return cls(
            id=data.get("id"),
            title=data.get("title", ""),
            username=data.get("username", ""),
            password=data.get("password", ""),
            url=data.get("url", ""),
            notes=data.get("notes", ""),
            category=data.get("category", "Other"),
            favorite=bool(data.get("favorite", False)),
            created_at=data.get("created_at", format_iso_datetime()),
            updated_at=data.get("updated_at", format_iso_datetime()),
        )


@dataclass
class VaultHealthStats:
    """Represents dashboard health statistics."""
    total_items: int = 0
    favorites_count: int = 0
    weak_count: int = 0
    medium_count: int = 0
    strong_count: int = 0
    reused_count: int = 0
