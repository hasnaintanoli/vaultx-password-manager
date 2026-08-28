"""
VaultX Authentication & Session Manager.
Handles vault initialization, authentication checks, key unwrapping, session locking,
and entry-level field encryption/decryption.
"""

import base64
from typing import Optional, Tuple, List, Dict, Any

from cryptography.fernet import InvalidToken

from app import config
from app.crypto import (
    generate_salt,
    generate_master_key,
    derive_kek,
    encrypt_string,
    decrypt_string
)
from app.database import DatabaseManager
from app.models import VaultEntry
from app.utils import logger


VERIFIER_CONST = "VAULTX_VERIFY_KEY_OK"


class AuthManager:
    """Manages active vault authentication session and active Vault Master Key (VMK)."""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self._active_vmk: Optional[bytes] = None
        self._incorrect_attempts: int = 0

    @property
    def incorrect_attempts(self) -> int:
        """Returns number of consecutive incorrect password attempts."""
        return self._incorrect_attempts

    def is_vault_created(self) -> bool:
        """Checks if a master vault exists in the database."""
        return self.db.is_vault_initialized()

    def is_unlocked(self) -> bool:
        """Checks if vault session is currently unlocked."""
        return self._active_vmk is not None

    def lock_vault(self) -> None:
        """Locks vault session and clears Vault Master Key from memory."""
        self._active_vmk = None
        logger.info("Vault session locked. Master key cleared from memory.")

    def create_vault(self, master_password: str) -> Tuple[bool, str]:
        """
        Initializes a new vault with the given master password.
        
        Steps:
        1. Validate password length.
        2. Generate 16-byte random salt.
        3. Derive Key Encryption Key (KEK) via Argon2id.
        4. Generate random 32-byte Vault Master Key (VMK).
        5. Encrypt VMK using KEK.
        6. Create verifier token by encrypting VERIFIER_CONST with VMK.
        7. Persist salt, encrypted VMK, and verifier token in SQLite.
        """
        if not master_password or len(master_password) < config.MIN_MASTER_PASSWORD_LENGTH:
            return False, f"Master password must be at least {config.MIN_MASTER_PASSWORD_LENGTH} characters long."

        try:
            salt = generate_salt()
            kek = derive_kek(master_password, salt)
            vmk = generate_master_key()

            # Encrypt base64-encoded VMK using KEK
            vmk_b64 = base64.b64encode(vmk).decode("utf-8")
            encrypted_vmk_str = encrypt_string(vmk_b64, kek)

            # Encrypt verifier constant with VMK
            verifier_token = encrypt_string(VERIFIER_CONST, vmk)

            # Persist in SQLite
            self.db.initialize_vault(salt, encrypted_vmk_str, verifier_token)

            # Set active session VMK
            self._active_vmk = vmk
            self._incorrect_attempts = 0

            logger.info("New vault successfully created and unlocked.")
            return True, "Vault created successfully."
        except Exception as e:
            logger.error(f"Error creating vault: {e}")
            return False, "Failed to create vault. Please check error logs."

    def unlock_vault(self, master_password: str) -> Tuple[bool, str]:
        """
        Attempts to unlock the vault with master_password.
        
        Steps:
        1. Fetch salt, encrypted VMK, verifier token from SQLite.
        2. Derive KEK via Argon2id using provided master_password and stored salt.
        3. Decrypt VMK using KEK.
        4. Verify VMK by decrypting verifier token.
        5. On match, unlock vault and cache VMK in memory.
        """
        if not master_password:
            return False, "Master password cannot be empty."

        metadata = self.db.get_metadata()
        if not metadata:
            return False, "Vault metadata not found. Vault may be uninitialized."

        try:
            salt = metadata["salt"]
            encrypted_vmk_str = metadata["encrypted_vmk"]
            verifier_token = metadata["verifier_token"]

            # Derive KEK from input password
            kek = derive_kek(master_password, salt)

            # Decrypt VMK
            vmk_b64 = decrypt_string(encrypted_vmk_str, kek)
            vmk = base64.b64decode(vmk_b64.encode("utf-8"))

            # Verify VMK by checking verifier token
            decrypted_verifier = decrypt_string(verifier_token, vmk)
            if decrypted_verifier == VERIFIER_CONST:
                self._active_vmk = vmk
                self._incorrect_attempts = 0
                logger.info("Vault successfully unlocked.")
                return True, "Vault unlocked successfully."
            else:
                self._incorrect_attempts += 1
                return False, "Incorrect master password."
        except InvalidToken:
            self._incorrect_attempts += 1
            return False, "Incorrect master password."
        except Exception as e:
            self._incorrect_attempts += 1
            logger.error(f"Failed unlock attempt: {e}")
            return False, "Incorrect master password or corrupted metadata."

    def encrypt_entry(self, entry: VaultEntry) -> Dict[str, Any]:
        """Encrypts fields of VaultEntry using the active VMK."""
        if not self.is_unlocked() or not self._active_vmk:
            raise ValueError("Vault is locked. Cannot encrypt entry.")

        return {
            "id": entry.id,
            "title_encrypted": encrypt_string(entry.title, self._active_vmk),
            "username_encrypted": encrypt_string(entry.username, self._active_vmk),
            "password_encrypted": encrypt_string(entry.password, self._active_vmk),
            "url_encrypted": encrypt_string(entry.url, self._active_vmk),
            "notes_encrypted": encrypt_string(entry.notes, self._active_vmk),
            "category": entry.category or "Other",
            "favorite": 1 if entry.favorite else 0,
            "created_at": entry.created_at,
            "updated_at": entry.updated_at
        }

    def decrypt_entry(self, row: Dict[str, Any]) -> VaultEntry:
        """Decrypts database row dictionary into a VaultEntry model."""
        if not self.is_unlocked() or not self._active_vmk:
            raise ValueError("Vault is locked. Cannot decrypt entry.")

        title = decrypt_string(row.get("title_encrypted", ""), self._active_vmk)
        username = decrypt_string(row.get("username_encrypted", ""), self._active_vmk)
        password = decrypt_string(row.get("password_encrypted", ""), self._active_vmk)
        url = decrypt_string(row.get("url_encrypted", ""), self._active_vmk)
        notes = decrypt_string(row.get("notes_encrypted", ""), self._active_vmk)

        return VaultEntry(
            id=row.get("id"),
            title=title,
            username=username,
            password=password,
            url=url,
            notes=notes,
            category=row.get("category", "Other"),
            favorite=bool(row.get("favorite", 0)),
            created_at=row.get("created_at", ""),
            updated_at=row.get("updated_at", "")
        )

    def decrypt_all_entries(self) -> List[VaultEntry]:
        """Fetches and decrypts all entries in the vault."""
        rows = self.db.get_all_entries()
        entries = []
        for row in rows:
            try:
                entries.append(self.decrypt_entry(row))
            except Exception as e:
                logger.error(f"Error decrypting entry ID {row.get('id')}: {e}")
        return entries
