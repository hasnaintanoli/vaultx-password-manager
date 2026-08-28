"""
VaultX Cryptographic Services.

SECURITY ARCHITECTURE OVERVIEW:
1. Master Password Key Derivation:
   - Uses Argon2id (via `argon2-cffi`), the state-of-the-art password hashing function.
   - Converts the master password into a 256-bit Key Encryption Key (KEK) using a unique 16-byte random salt.
   
2. Vault Master Key (VMK):
   - A cryptographically random 256-bit key generated once at vault setup using `secrets.token_bytes(32)`.
   - Used for encrypting and decrypting all sensitive vault fields (passwords, usernames, notes, URLs).
   - Encrypted with the KEK and stored in SQLite `vault_metadata`.
   
3. Field & Data Encryption:
   - Uses Fernet authenticated encryption (AES-128-CBC + HMAC-SHA256 with 128-bit IV and PKCS7 padding).
   - Ensures both Confidentiality and Authenticity/Integrity of stored data.
"""

import base64
import json
import secrets
from typing import Dict, List, Any, Tuple
import argon2
from cryptography.fernet import Fernet, InvalidToken

from app import config
from app.utils import logger


def generate_salt(length: int = config.ARGON2_SALT_LEN) -> bytes:
    """Generates a cryptographically secure random salt."""
    return secrets.token_bytes(length)


def generate_master_key() -> bytes:
    """Generates a cryptographically secure 256-bit Vault Master Key (VMK)."""
    return secrets.token_bytes(config.ARGON2_KEY_LEN)


def derive_kek(master_password: str, salt: bytes) -> bytes:
    """
    Derives a 256-bit Key Encryption Key (KEK) from the user's master password using Argon2id.
    
    SECURITY NOTE: Argon2id provides strong resistance against GPU/ASIC hardware attacks
    and side-channel memory attacks.
    """
    if isinstance(master_password, str):
        password_bytes = master_password.encode("utf-8")
    else:
        password_bytes = master_password

    # Low-level raw hash calculation using Argon2id
    kek = argon2.low_level.hash_secret_raw(
        secret=password_bytes,
        salt=salt,
        time_cost=config.ARGON2_TIME_COST,
        memory_cost=config.ARGON2_MEMORY_COST,
        parallelism=config.ARGON2_PARALLELISM,
        hash_len=config.ARGON2_KEY_LEN,
        type=argon2.low_level.Type.ID
    )
    return kek


def _get_fernet_instance(key_32_bytes: bytes) -> Fernet:
    """Creates a Fernet cipher instance from a 32-byte key."""
    b64_key = base64.urlsafe_b64encode(key_32_bytes)
    return Fernet(b64_key)


def encrypt_string(plaintext: str, key_32_bytes: bytes) -> str:
    """
    Encrypts a plaintext string using Fernet authenticated encryption.
    Returns base64-encoded ciphertext string.
    """
    if plaintext is None:
        plaintext = ""
    f = _get_fernet_instance(key_32_bytes)
    token_bytes = f.encrypt(plaintext.encode("utf-8"))
    return token_bytes.decode("utf-8")


def decrypt_string(ciphertext_token: str, key_32_bytes: bytes) -> str:
    """
    Decrypts a Fernet ciphertext token using the specified 32-byte key.
    
    Raises:
        InvalidToken: If key is wrong or data has been tampered with.
    """
    if not ciphertext_token:
        return ""
    f = _get_fernet_instance(key_32_bytes)
    decrypted_bytes = f.decrypt(ciphertext_token.encode("utf-8"))
    return decrypted_bytes.decode("utf-8")


def create_encrypted_backup(entries: List[Dict[str, Any]], backup_password: str) -> str:
    """
    Creates an encrypted backup JSON string (.vaultx contents).
    Derives a fresh key from backup_password using Argon2id and encrypts all entries.
    """
    backup_salt = generate_salt()
    backup_kek = derive_kek(backup_password, backup_salt)

    payload = {
        "version": 1,
        "app": config.APP_NAME,
        "entries": entries
    }
    json_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    
    f = _get_fernet_instance(backup_kek)
    encrypted_token = f.encrypt(json_bytes).decode("utf-8")

    backup_file_content = {
        "vaultx_backup_version": 1,
        "salt_b64": base64.b64encode(backup_salt).decode("utf-8"),
        "encrypted_data": encrypted_token
    }

    return json.dumps(backup_file_content, indent=2)


def restore_encrypted_backup(backup_json_str: str, backup_password: str) -> List[Dict[str, Any]]:
    """
    Decrypts and validates an encrypted backup JSON string.
    
    Returns:
        List of entry dictionaries on success.
        
    Raises:
        ValueError: If format is invalid or decryption fails (wrong password).
    """
    try:
        container = json.loads(backup_json_str)
        if "salt_b64" not in container or "encrypted_data" not in container:
            raise ValueError("Invalid backup file format.")

        salt = base64.b64decode(container["salt_b64"])
        encrypted_token = container["encrypted_data"]

        backup_kek = derive_kek(backup_password, salt)
        f = _get_fernet_instance(backup_kek)

        decrypted_bytes = f.decrypt(encrypted_token.encode("utf-8"))
        payload = json.loads(decrypted_bytes.decode("utf-8"))

        if not isinstance(payload, dict) or "entries" not in payload:
            raise ValueError("Backup payload is corrupted or incomplete.")

        return payload["entries"]
    except InvalidToken:
        raise ValueError("Incorrect backup password or corrupted backup file.")
    except Exception as e:
        if isinstance(e, ValueError):
            raise
        logger.error(f"Backup restoration error: {e}")
        raise ValueError("Failed to restore backup file. Ensure it is a valid VaultX backup.")
