# VaultX 🔐
> **Your passwords. Secured locally.**

[![Release](https://img.shields.io/github/v/release/hasnaintanoli/vaultx-password-manager?color=2563eb&label=Latest%20Release)](https://github.com/hasnaintanoli/vaultx-password-manager/releases/latest)
[![Python](https://img.shields.io/badge/Python-3.13%2B-blue.svg?logo=python&logoColor=white)](https://python.org)
[![GUI](https://img.shields.io/badge/GUI-CustomTkinter-blueviolet.svg)](https://github.com/TomSchimansky/CustomTkinter)
[![Security](https://img.shields.io/badge/Encryption-Argon2id%20%2B%20AES--128--CBC-success.svg)](https://cryptography.io)
[![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?logo=windows&logoColor=white)](https://github.com/hasnaintanoli/vaultx-password-manager/releases/latest)

[**📥 Download VaultX for Windows (v1.0.0 Setup Installer)**](https://github.com/hasnaintanoli/vaultx-password-manager/releases/download/v1.0.0/VaultX_Setup_v1.0.0.exe)

VaultX is a modern, production-quality, privacy-first local password manager desktop application built with Python 3.13+, CustomTkinter, and SQLite. VaultX operates 100% offline with zero network calls, zero external server dependencies, and zero plaintext credential storage.

---

## 🌟 Key Features

* **100% Offline & Local**: Your vault data never leaves your device. No cloud sync, no tracking, no telemetry, and zero external server calls.
* **Argon2id Key Derivation**: Uses Argon2id (via `argon2-cffi`), the state-of-the-art password hashing algorithm, to derive 256-bit Key Encryption Keys (KEK) with cryptographically random salts.
* **Fernet Authenticated Encryption**: Field-level authenticated encryption (AES-128-CBC + HMAC-SHA256) protects usernames, passwords, URLs, and secure notes individually at rest.
* **Cryptographically Secure Password Generator**: Generates entropy-rich passwords using Python's `secrets` module (never using weak PRNGs) with customizable character sets and ambiguous character exclusion.
* **Modern Premium Interface**: Inspired by 1Password, Bitwarden, and Linear. Dark-first modern design with custom cards, strength progress bars, pill badges, and toasts.
* **Instant Dynamic Search**: Filter items instantly by Title, Username, Website URL, or Category without exposing plaintext passwords.
* **Dashboard Health Statistics**: Real-time non-sensitive vault statistics, favorite tracking, and weak password identification.
* **Clipboard Auto-Clear**: Automatically wipes copied passwords from system clipboard after a configurable timeout (e.g., 30 seconds).
* **Auto-Lock Security**: Inactivity timer automatically locks the vault and purges decryption keys from memory upon user idle timeout.
* **Encrypted Backups**: Export and restore password vaults safely using encrypted `.vaultx` files protected by Argon2id password-based encryption.

---

## 🛠️ Technology Stack

* **Language**: Python 3.13+
* **GUI Framework**: CustomTkinter
* **Database**: SQLite3 (with parameterized queries)
* **Cryptography & KDF**: `cryptography` & `argon2-cffi`
* **Secure Random Generator**: `secrets` module
* **Image & Icon Processing**: `pillow`
* **Clipboard Management**: `pyperclip`
* **Installer Engine**: Inno Setup 6 (Ultra LZMA2 compression)
* **Executable Packager**: PyInstaller

---

## 📁 Project Structure

```text
vaultx-password-manager/
│
├── main.py                    # Application launcher & window manager
├── requirements.txt           # Python dependency requirements
├── pyrightconfig.json         # Python language server configuration
├── README.md                  # Comprehensive documentation
├── .gitignore                 # Git exclusion rules
│
├── app/                       # Business Logic & Backend Core
│   ├── __init__.py
│   ├── config.py              # App constants, design system palette, persistent storage paths
│   ├── database.py            # SQLite manager with parameterized queries
│   ├── crypto.py              # Argon2id KDF, Fernet encryption, backup handler
│   ├── auth.py                # Session authentication manager & VMK caching
│   ├── password_generator.py  # Secrets-driven password generator & evaluator
│   ├── models.py              # VaultEntry and VaultHealthStats dataclasses
│   └── utils.py               # Logging, clipboard auto-clear, date sanitization
│
├── ui/                        # CustomTkinter User Interface Components
│   ├── __init__.py
│   ├── components.py          # Modern cards, badges, progress bars, toast alerts, dialogs
│   ├── login_window.py        # First-launch setup & unlock screen
│   ├── main_window.py         # Shell with sidebar navigation, search bar header & auto-lock
│   ├── vault_view.py          # Main vault items list, health dashboard & filters
│   ├── add_entry.py           # Add password entry modal dialog
│   ├── edit_entry.py          # View, edit, copy, and delete entry modal dialog
│   ├── password_generator.py  # Dedicated password generator view
│   └── settings.py            # Security preferences & backup/restore view
│
├── assets/                    # Application Branding Assets
│   ├── icon.png               # High-resolution PNG logo
│   └── icon.ico               # Multi-resolution Windows native icon
│
├── installer/                 # Windows Installer Script
│   └── vaultx_setup.iss       # Inno Setup 6 compilation script
│
├── data/                      # Local database directory (.gitkeep)
│   └── .gitkeep
│
├── exports/                   # Encrypted .vaultx backups (.gitkeep)
│   └── .gitkeep
│
└── logs/                      # Application diagnostics (.gitkeep)
    └── .gitkeep
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

3. **Memory Safety & Process Isolation**:
   * Master Key (VMK) is kept in memory only during active unlocked sessions.
   * Locking the vault clears the VMK reference and returns the application to the locked authentication state.

---

## 💾 Persistent Database Storage

VaultX automatically handles persistent storage based on execution mode:

| Mode | Database Storage Path |
|---|---|
| **Development (`python main.py`)** | `data/vault.db` (local project folder) |
| **Installed Application (`.exe`)** | `%APPDATA%\VaultX\data\vault.db` (`C:\Users\<User>\AppData\Roaming\VaultX\data\vault.db`) |

> **Note**: Storing database files in standard `%APPDATA%` ensures user passwords and settings are preserved permanently across app updates and reinstalls.

---

## ⚡ Installation & Development Setup

### 1. Clone the Repository

```bash
git clone https://github.com/hasnaintanoli/vaultx-password-manager.git
cd vaultx-password-manager
```

### 2. Create Python Virtual Environment

**Windows:**
```powershell
python -m venv .venv
.\.venv\Scripts\activate
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

### 4. Run the Application

```bash
python main.py
```

---

## 📦 Building Executable & Setup Installer

### Build Standalone `.exe` (PyInstaller)

To compile a single portable Windows executable with embedded custom icons:

```powershell
python -m PyInstaller --noconsole --onefile --name "VaultX" --icon "assets/icon.ico" --add-data "assets;assets" --collect-all customtkinter --clean main.py
```

The resulting executable is generated at: `dist/VaultX.exe`

---

### Build Windows Setup Installer (Inno Setup)

To build a professional Windows installer (`VaultX_Setup_v1.0.0.exe`) with Desktop shortcuts, Start Menu integration, and clean uninstaller:

```powershell
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\vaultx_setup.iss
```

The resulting installer is generated at: `dist/VaultX_Setup_v1.0.0.exe`

---

## 🔄 Backup & Restoration

VaultX supports encrypted vault backups (`.vaultx`):

1. **Export Backup**:
   * Navigate to **Settings** → **Encrypted Backup & Restore**.
   * Click **Create Encrypted Backup**.
   * Choose a password for the backup file.
   * VaultX encrypts all vault items into an Argon2id-protected `.vaultx` JSON container.

2. **Restore Backup**:
   * Click **Restore Encrypted Backup**.
   * Select your `.vaultx` backup file and enter the backup password.
   * VaultX validates integrity and safely imports restored entries into your local vault.

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
