# VaultX 🔐
> **Your passwords. Secured locally.**

VaultX is a modern, production-quality, privacy-first local password manager desktop application built with Python 3.13+, CustomTkinter, and SQLite. VaultX operates 100% offline with zero network calls, zero external server dependencies, and zero plaintext credential storage.

---

## 🌟 Key Features

* **100% Offline & Local**: Your vault data never leaves your device. No cloud sync, no tracking, no external server calls.
* **Argon2id Key Derivation**: Uses Argon2id (via `argon2-cffi`), the state-of-the-art password hashing function, to derive 256-bit Key Encryption Keys (KEK) from your master password.
* **Fernet Authenticated Encryption**: Field-level authenticated encryption (AES-128-CBC + HMAC-SHA256) protects usernames, passwords, URLs, and secure notes.
* **Cryptographically Secure Password Generator**: Generates entropy-rich passwords using Python's `secrets` module (never using weak PRNGs).
* **Modern Premium Interface**: Inspired by 1Password, Bitwarden, and Linear. Dark mode design with visual strength bars, custom cards, pill badges, and toasts.
* **Instant Dynamic Search**: Filter items instantly by Title, Username, Website URL, or Category without exposing plaintext passwords.
* **Dashboard Health Statistics**: Real-time non-sensitive vault statistics, favorite tracking, and weak password identification.
* **Clipboard Auto-Clear**: Automatically wipes copied passwords from system clipboard after a configurable timeout (e.g., 30 seconds).
* **Auto-Lock Security**: Automatically locks the vault after a specified period of user inactivity.
* **Encrypted Backups**: Export and restore password vaults safely using encrypted `.vaultx` files protected by Argon2id.

---

## 🛠️ Technology Stack

* **Language**: Python 3.13+
* **GUI Framework**: CustomTkinter
* **Database**: SQLite3
* **Cryptography & KDF**: `cryptography` & `argon2-cffi`
* **Secure Random Generator**: `secrets` module
* **Clipboard Management**: `pyperclip`
* **Test Suite**: `pytest`

---

## 📁 Project Structure

```text
VaultX/
│
├── main.py                    # Application launcher & window manager
├── requirements.txt           # Python dependency requirements
├── README.md                  # Comprehensive documentation
├── .gitignore                 # Git ignore patterns
│
├── app/                       # Business Logic & Backend Core
│   ├── __init__.py
│   ├── config.py              # App constants, design system palette, security settings
│   ├── database.py            # SQLite manager with parameterized queries
│   ├── crypto.py              # Argon2id KDF, Fernet encryption, backup handler
│   ├── auth.py                # Session authentication manager & VMK caching
│   ├── password_generator.py  # Secrets-driven password generator & evaluator
│   ├── models.py              # VaultEntry and VaultHealthStats dataclasses
│   └── utils.py               # Logging, clipboard auto-clear, date sanitization
│
├── ui/                        # CustomTkinter User Interface Components
│   ├── __init__.py
│   ├── components.py          # Modern cards, badges, progress bars, toast alerts
│   ├── login_window.py        # First-launch setup & unlock screen
│   ├── main_window.py         # Shell with sidebar navigation, search bar header & auto-lock
│   ├── vault_view.py          # Main vault items list, health dashboard & filters
│   ├── add_entry.py           # Add password entry modal dialog
│   ├── edit_entry.py          # View, edit, copy, and delete entry modal dialog
│   ├── password_generator.py  # Dedicated password generator view
│   └── settings.py            # Security preferences & backup/restore view
│
├── data/                      # Local SQLite database storage (.gitkeep)
│   └── .gitkeep
│
├── exports/                   # Encrypted .vaultx backups (.gitkeep)
│   └── .gitkeep
│
└── tests/                     # Automated Pytest Suite
    ├── test_crypto.py
    ├── test_database.py
    └── test_password_generator.py
```

---

## 🔐 Security & Cryptographic Architecture

```text
Master Password
       ↓
Argon2id KDF (Time: 3, Memory: 64MB, Parallelism: 4) + 16-byte Random Salt
       ↓
256-bit Key Encryption Key (KEK)
       ↓
Unwraps Encrypted Vault Master Key (VMK)
       ↓
Fernet Cipher (AES-128-CBC + HMAC-SHA256)
       ↓
Encrypts/Decrypts Vault Fields at Rest in SQLite
```

1. **Master Password Protection**:
   * Minimum master password length enforced: 12 characters.
   * Master password is **never stored** in plaintext or written to disk.
   * Only a verifier token (`"VAULTX_VERIFY_KEY_OK"`) encrypted under the VMK is stored to validate authentication.

2. **Database Field Encryption**:
   * All sensitive columns (`title_encrypted`, `username_encrypted`, `password_encrypted`, `url_encrypted`, `notes_encrypted`) are stored as Fernet tokens in SQLite.
   * SQL queries strictly use parameterized statements (`?`) to eliminate SQL injection risks.

3. **Memory Safety**:
   * Master Key (VMK) is kept in memory only during active unlocked sessions.
   * Locking the vault clears the VMK reference and returns the application to the locked authentication state.

---

## ⚡ Installation & Setup

### 1. Clone the repository

```bash
git clone https://github.com/hasnaintanoli/vaultx-password-manager.git
cd vaultx-password-manager
```

### 2. Create Python Virtual Environment

**Windows:**
```cmd
python -m venv .venv
.venv\Scripts\activate
```

**Linux / macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 🚀 Running the Application

Launch VaultX using Python:

```bash
python main.py
```

---

## 🧪 Running Automated Tests

Run the full automated pytest suite:

```bash
python -m pytest
```

Output:
```text
tests/test_crypto.py .....                                               [ 41%]
tests/test_database.py ...                                               [ 66%]
tests/test_password_generator.py ....                                    [100%]
============================= 12 passed in 1.69s ==============================
```

---

## 📦 Backup & Restoration

VaultX supports encrypted vault backups (`.vaultx`):

1. **Export Backup**:
   * Go to **Settings** → **Encrypted Backup & Restore**.
   * Click **Create Encrypted Backup**.
   * Choose a password for the backup file.
   * VaultX encrypts all vault items into an Argon2id-protected `.vaultx` JSON bundle.

2. **Restore Backup**:
   * Click **Restore Encrypted Backup**.
   * Select your `.vaultx` backup file and enter the backup password.
   * VaultX validates integrity and safely imports restored entries.

---

## 🔮 Future Expansion Architecture

VaultX is architected to seamlessly accommodate future features:
* 🔑 **TOTP 2FA Authenticator**: Storing and generating 6-digit 2FA codes.
* 💳 **Credit Card & Identity Vault**: Secure storage for financial cards and IDs.
* 🌐 **Browser Extension Messaging**: Local Native Messaging host protocol for auto-fill capabilities.
* 📊 **Breach Monitoring**: Offline checking against HIBP K-Anonymity hash prefixes.

---

## ⚠️ Security Notice & Limitations

> [!IMPORTANT]
> **Educational & Portfolio Notice**: VaultX is developed as a serious portfolio project demonstrating modern cryptographic design, desktop UI development, and clean Python architecture. While designed following industry security best practices, it has not undergone an independent professional security audit. Use it responsibly.
