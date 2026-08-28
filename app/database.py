"""
VaultX Database Management Layer.
Handles local SQLite database initialization, metadata storage, parameterized CRUD operations,
and configuration settings storage.
"""

import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any

from app import config
from app.utils import logger, format_iso_datetime


class DatabaseManager:
    """Manages SQLite database connection and operations safely using parameterized queries."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or config.DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Creates a new SQLite database connection with row factory enabled."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Initializes database schema if tables do not already exist."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Table for Vault Master Metadata (Salt, Encrypted VMK, Verifier Token)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS vault_metadata (
                        id INTEGER PRIMARY KEY CHECK (id = 1),
                        salt BLOB NOT NULL,
                        encrypted_vmk TEXT NOT NULL,
                        verifier_token TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                """)

                # Table for Vault Entries (Encrypted sensitive fields)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS vault_entries (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title_encrypted TEXT NOT NULL,
                        username_encrypted TEXT,
                        password_encrypted TEXT NOT NULL,
                        url_encrypted TEXT,
                        notes_encrypted TEXT,
                        category TEXT NOT NULL DEFAULT 'Other',
                        favorite INTEGER NOT NULL DEFAULT 0,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                """)

                # Table for Application Settings
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS app_settings (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL
                    )
                """)

                conn.commit()
                logger.info("Database schema initialized successfully.")
        except sqlite3.Error as e:
            logger.error(f"Failed to initialize database schema: {e}")
            raise

    def is_vault_initialized(self) -> bool:
        """Checks if a vault master password / metadata record exists."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM vault_metadata WHERE id = 1")
                return cursor.fetchone() is not None
        except sqlite3.Error as e:
            logger.error(f"Error checking vault initialization: {e}")
            return False

    def initialize_vault(self, salt: bytes, encrypted_vmk_str: str, verifier_token: str) -> None:
        """Stores initial vault metadata record."""
        now = format_iso_datetime()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO vault_metadata (id, salt, encrypted_vmk, verifier_token, created_at, updated_at)
                VALUES (1, ?, ?, ?, ?, ?)
            """, (salt, encrypted_vmk_str, verifier_token, now, now))
            conn.commit()
            logger.info("Vault metadata record initialized.")

    def get_metadata(self) -> Optional[Dict[str, Any]]:
        """Retrieves stored vault metadata (salt, encrypted_vmk, verifier_token)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT salt, encrypted_vmk, verifier_token, created_at, updated_at FROM vault_metadata WHERE id = 1")
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None

    def add_entry(self, entry_data: Dict[str, Any]) -> int:
        """
        Inserts a new encrypted vault entry into SQLite using parameterized queries.
        Returns the generated entry ID.
        """
        now = format_iso_datetime()
        created_at = entry_data.get("created_at") or now
        updated_at = entry_data.get("updated_at") or now

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO vault_entries (
                    title_encrypted, username_encrypted, password_encrypted,
                    url_encrypted, notes_encrypted, category, favorite, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entry_data.get("title_encrypted", ""),
                entry_data.get("username_encrypted", ""),
                entry_data.get("password_encrypted", ""),
                entry_data.get("url_encrypted", ""),
                entry_data.get("notes_encrypted", ""),
                entry_data.get("category", "Other"),
                1 if entry_data.get("favorite") else 0,
                created_at,
                updated_at
            ))
            conn.commit()
            return cursor.lastrowid

    def get_all_entries(self) -> List[Dict[str, Any]]:
        """Fetches all encrypted entries from the database."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, title_encrypted, username_encrypted, password_encrypted,
                       url_encrypted, notes_encrypted, category, favorite, created_at, updated_at
                FROM vault_entries ORDER BY updated_at DESC
            """)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_entry(self, entry_id: int) -> Optional[Dict[str, Any]]:
        """Fetches a single entry by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, title_encrypted, username_encrypted, password_encrypted,
                       url_encrypted, notes_encrypted, category, favorite, created_at, updated_at
                FROM vault_entries WHERE id = ?
            """, (entry_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None

    def update_entry(self, entry_id: int, entry_data: Dict[str, Any]) -> bool:
        """Updates an existing vault entry."""
        now = format_iso_datetime()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE vault_entries SET
                    title_encrypted = ?,
                    username_encrypted = ?,
                    password_encrypted = ?,
                    url_encrypted = ?,
                    notes_encrypted = ?,
                    category = ?,
                    favorite = ?,
                    updated_at = ?
                WHERE id = ?
            """, (
                entry_data.get("title_encrypted", ""),
                entry_data.get("username_encrypted", ""),
                entry_data.get("password_encrypted", ""),
                entry_data.get("url_encrypted", ""),
                entry_data.get("notes_encrypted", ""),
                entry_data.get("category", "Other"),
                1 if entry_data.get("favorite") else 0,
                now,
                entry_id
            ))
            conn.commit()
            return cursor.rowcount > 0

    def delete_entry(self, entry_id: int) -> bool:
        """Deletes an entry by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM vault_entries WHERE id = ?", (entry_id,))
            conn.commit()
            return cursor.rowcount > 0

    def set_favorite(self, entry_id: int, favorite: bool) -> bool:
        """Updates favorite flag for an entry."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE vault_entries SET favorite = ? WHERE id = ?", (1 if favorite else 0, entry_id))
            conn.commit()
            return cursor.rowcount > 0

    def get_setting(self, key: str, default: str = "") -> str:
        """Reads a setting value from app_settings."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM app_settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            if row:
                return row["value"]
            return default

    def set_setting(self, key: str, value: str) -> None:
        """Sets a setting value in app_settings."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO app_settings (key, value) VALUES (?, ?)", (key, str(value)))
            conn.commit()

    def replace_all_entries(self, encrypted_entries: List[Dict[str, Any]]) -> None:
        """Replaces all current vault entries with a restored set within a transaction."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM vault_entries")
            for entry in encrypted_entries:
                cursor.execute("""
                    INSERT INTO vault_entries (
                        title_encrypted, username_encrypted, password_encrypted,
                        url_encrypted, notes_encrypted, category, favorite, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    entry.get("title_encrypted", ""),
                    entry.get("username_encrypted", ""),
                    entry.get("password_encrypted", ""),
                    entry.get("url_encrypted", ""),
                    entry.get("notes_encrypted", ""),
                    entry.get("category", "Other"),
                    1 if entry.get("favorite") else 0,
                    entry.get("created_at", format_iso_datetime()),
                    entry.get("updated_at", format_iso_datetime())
                ))
            conn.commit()
            logger.info("Restored entries replaced in database successfully.")
