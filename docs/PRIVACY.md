# Privacy Statement — ORBIT

**Everything ORBIT does happens on your machine. No data ever leaves it.**

---

## What ORBIT does NOT do

- Does not transmit findings, credentials, or configuration data to any server.
- Does not collect telemetry, usage statistics, or analytics.
- Does not check for updates by contacting any remote server.
- Does not use third-party crash reporting, logging services, or cloud storage.
- Does not embed tracking pixels, beacons, or identifiers.

---

## Network activity

ORBIT itself makes **zero outbound network connections**.

The only network activity that occurs when using ORBIT is:

| Activity | Who initiates it | When |
|----------|-----------------|------|
| Microsoft 365 API calls | The tool ORBIT launches (ScubaGear, Maester, etc.) | During a run |
| PowerShell Gallery downloads | `pwsh` / `Install-Module` | Only when you press Install/Update in the Installer screen |
| PyPI downloads | `pip` | Only when you press Install/Update in the Installer screen |
| OPA binary download | ScubaGear's `Initialize-SCuBA` | Only during ScubaGear first-time setup |

All of the above are standard, expected operations of the underlying tools — not initiated by ORBIT's own code.

---

## What is stored on your machine

| Data | Location | Format | Encrypted? |
|------|----------|--------|-----------|
| Credentials (Tenant ID, App ID, secrets) | OS keychain (`orbit-m365` service) | Keychain-protected | Yes — by OS |
| Credentials (fallback if no keychain) | `~/.orbit/secrets.enc` | Fernet (AES-256-CBC) with PBKDF2-HMAC-SHA256 (600,000 iterations), file mode 0600 | Yes |
| Tool output (raw) | `output/YYYY-MM-DD_HH-MM/<tool>/` or your chosen directory | As produced by each tool (HTML, JSON, CSV) | Optional |
| ORBIT summary report | `output/YYYY-MM-DD_HH-MM/ORBIT_Summary.pdf` and `.docx` | Plain PDF / DOCX | Optional |
| Encrypted output bundle (opt-in) | `<run folder>.orbit.zip` | ZIP then Fernet-encrypted with your passphrase | Yes |

**Not stored anywhere:**
- Passphrases (held in memory for the session only; not recoverable if forgotten)
- Plaintext credentials in any file
- Credentials in process arguments (secrets are passed via environment variables of child processes only — never in `argv`, which `ps`/`top` can reveal)
- Log files containing secrets (masked with `***` in all log output)

---

## Credential storage detail

ORBIT uses the `keyring` library, which delegates to:

| OS | Backend |
|----|---------|
| Windows | Windows Credential Manager |
| macOS | macOS Keychain |
| Linux (GNOME) | libsecret / GNOME Keyring |
| Linux (KDE) | KWallet |
| Linux (no keyring) | Fernet-encrypted fallback file |

The service name stored in the keychain is `orbit-m365`. The username key is the tool name (e.g., `scubagear`, `maester`). The secret value is a JSON blob containing the tool's credentials, encrypted by the OS keychain before writing to disk.

The Fernet fallback uses a key derived from your passphrase via PBKDF2-HMAC-SHA256 with a random 16-byte salt and 600,000 iterations. The salt is stored alongside the encrypted blob. The passphrase itself is never stored.

---

## Tool output sensitivity

The output of ScubaGear, Maester, Monkey365, and other tools contains **detailed information about your Microsoft 365 tenant configuration**. This data may include:

- Names and states of Conditional Access policies
- User and admin account details (display names, UPNs)
- Application and service principal names
- Licence and feature states
- Security and compliance policy configurations

**Treat tool output as sensitive data.** Store it in a location appropriate to your organisation's data classification policies. Use ORBIT's optional output encryption if the assessment data should be protected at rest.

---

## Third-party tool privacy

Each tool ORBIT launches has its own privacy and data handling characteristics:

- **ScubaGear and Maester** connect to Microsoft 365 APIs. Microsoft's data handling is governed by your Microsoft service agreement and applicable data processing agreements.
- **ROADtools** reads Entra ID directory data and stores it in a local SQLite database. No data leaves your machine via ROADtools.
- **Hawk** reads Exchange and Entra audit logs and writes them to local files. No data leaves your machine via Hawk.
- **Monkey365** reads Microsoft API data and writes reports locally. No data leaves your machine via Monkey365.

Review each tool's documentation for current information on their data handling.

---

## Open source and auditability

ORBIT's source code is fully open. You can review exactly what it does at:

https://github.com/OrbitalSecurity/OrbitM365

There are no compiled binaries, obfuscated code, or pre-built executables in ORBIT itself. You run it directly from source.

---

*This privacy statement describes ORBIT v1.0.0 as of November 2026. It will be updated if the software's data handling changes.*
