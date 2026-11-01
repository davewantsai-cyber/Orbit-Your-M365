# Installation Guide — ORBIT

## Before you start

ORBIT is a Python application that **launches** other security tools. Prerequisites depend on which tools you want to run.

| Prerequisite | Required for |
|-------------|-------------|
| Python 3.10+ | ORBIT itself |
| PowerShell 7 | ScubaGear, Maester, Monkey365, Hawk |
| Windows 10/11 | ScubaGear (Windows only) |
| M365 App Registration | Non-interactive tool runs |
| Global Administrator or delegated read roles | Most tools |

---

## Windows 10/11 (Primary)

### 1. Install Python 3.10+

Download from [python.org](https://www.python.org/downloads/). During install, tick **"Add Python to PATH"**.

Verify: `python --version`

### 2. Install PowerShell 7

```powershell
winget install Microsoft.PowerShell
```

Or download from [github.com/PowerShell/PowerShell/releases](https://github.com/PowerShell/PowerShell/releases).

Verify: `pwsh --version`

### 3. Clone and install ORBIT

```powershell
git clone https://github.com/YOUR_USERNAME/orbit-m365.git
cd orbit-m365
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
```

### 4. Verify

```powershell
pytest tests/ -v       # all 36 tests should pass
python orbit.py --help
python orbit.py --dry-run   # launches TUI in dry-run mode, no tenant needed
```

### 5. Run ORBIT for real

Open **PowerShell 7 as Administrator** (right-click → Run as Administrator). ScubaGear and Maester need elevated rights for some operations.

```powershell
python orbit.py
```

Use the **Installer** screen to install each tool, then **Credentials** to enter your M365 connection details.

### PowerShell execution policy

If you see execution policy errors:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## macOS

```bash
# Python 3.10+ (or use pyenv / brew)
brew install python@3.12

# PowerShell 7 (optional — needed for Maester, Monkey365, Hawk)
brew install powershell

# Clone and install
git clone https://github.com/YOUR_USERNAME/orbit-m365.git
cd orbit-m365
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Verify
pytest tests/ -v
python orbit.py --dry-run
```

**Note:** ScubaGear is Windows-only. ORBIT shows it as "incompatible OS" on macOS. Maester, Monkey365, ROADtools, and Hawk all work on macOS with PowerShell 7.

---

## Linux

```bash
# Python 3.10+ (apt example)
sudo apt install python3.12 python3.12-venv

# PowerShell 7 — see Microsoft's package repo:
# https://learn.microsoft.com/en-us/powershell/scripting/install/installing-powershell-on-linux

git clone https://github.com/YOUR_USERNAME/orbit-m365.git
cd orbit-m365
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

pytest tests/ -v
python orbit.py --dry-run
```

**Keychain on Linux:** ORBIT uses `libsecret` via the `keyring` library (GNOME Keyring / KWallet). If neither is available, ORBIT falls back to a Fernet-encrypted file at `~/.orbit/secrets.enc` and prompts for a passphrase.

---

## Setting up an M365 App Registration

For non-interactive / automated runs (recommended), create an App Registration in Entra ID:

1. Go to [portal.azure.com](https://portal.azure.com) → **Entra ID** → **App registrations** → **New registration**.
2. Name it (e.g., `ORBIT-Assessment`), choose **Accounts in this organisational directory only**, no redirect URI.
3. Note the **Application (client) ID** and **Directory (tenant) ID**.
4. Under **Certificates & secrets** → create a **Client secret** (or upload a certificate).
5. Under **API permissions**, add the permissions required by each tool you want to run. Refer to [docs/TOOLS.md](TOOLS.md) and each tool's official documentation for current permission lists.
6. Grant admin consent for the permissions.

Enter the Tenant ID, App ID, and client secret (or certificate thumbprint) in ORBIT's **Credentials** screen.

---

## Installing the security tools

Use ORBIT's **Installer** screen, or install manually:

```powershell
# ScubaGear
Install-Module -Name ScubaGear -Scope CurrentUser
Initialize-SCuBA        # downloads OPA binary

# Maester
Install-Module -Name Maester -Scope CurrentUser

# Monkey365
Install-Module -Name monkey365 -Scope CurrentUser

# Hawk
Install-Module -Name Hawk -Scope CurrentUser
```

```bash
# ROADtools
pip install roadrecon
```

---

## Testing without a tenant

See the [Testing section in README.md](../README.md#how-to-test-without-a-work-tenant) for options including dry-run mode, the M365 E5 30-day trial, and the Microsoft 365 Developer Program sandbox.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `pwsh: command not found` | Install PowerShell 7 and ensure it's on PATH |
| ScubaGear shows "incompatible OS" | Expected on macOS/Linux — ScubaGear is Windows-only |
| Keychain not available | ORBIT will use the encrypted file fallback; set a strong passphrase |
| `ModuleNotFoundError: No module named 'textual'` | Activate the venv: `source .venv/bin/activate` (Linux/macOS) or `.venv\Scripts\activate` (Windows) |
| Banner looks garbled | Use a modern terminal: Windows Terminal, iTerm2, or a terminal with full Unicode support |
| Tests fail with import errors | Ensure you installed with `pip install -e ".[dev]"` not `pip install -e .` |
