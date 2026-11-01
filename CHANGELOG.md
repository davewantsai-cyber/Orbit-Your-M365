# Changelog

## [1.1.0] — 2026-11-01

### Added
- Client name field on Output screen — stamped on PDF/DOCX report cover (blank defaults to "Confidential")
- Run history tracking (`~/.orbit/history.json`) — Home screen shows last run date, score, and delta (↑/↓)
- Config file (`~/.orbit/config.toml`) — persists output directory, format selection, tool selection, email settings across sessions
- OS completion notification via `plyer` — fires when run finishes, respects `os_notify` config flag
- `--headless --json` mode — run without TUI, outputs machine-readable JSON to stdout; exit 1 on failure
- `--tools` flag for headless mode — e.g. `--tools scubagear,maester`
- Email on completion — SMTP config screen (host, port, TLS, From, To, CC), HTML body with score and top findings, PDF attached, sends automatically after run if enabled
- "Email results when complete" toggle on Run screen
- GitHub Actions CI — runs 58 tests across Python 3.10, 3.11, 3.12 on every push/PR
- `SECURITY.md` — responsible disclosure policy
- `CONTRIBUTING.md` — contribution guide and code standards
- GitHub issue templates — bug report and feature request

### Improved
- CVE/NIST mappings expanded from 8 → 31 controls covering full CISA SCuBA baseline:
  - Entra ID: legacy auth, admin MFA, user MFA, phishing-resistant MFA, Conditional Access, PIM, guest invite, SSPR, Identity Protection, app consent, OAuth apps, break-glass accounts, cloud-only admins, GA count
  - Exchange Online: external forwarding, Safe Links, Safe Attachments, anti-phishing, DMARC, DKIM, SPF
  - SharePoint: external sharing, guest expiry
  - Teams: external access, meeting security
  - Power Platform: DLP policies, tenant isolation
  - Intune: device compliance

### Tests
- 36 → 58 passing

---

## [1.0.0] — 2026-11-01

### Added
- Animated Textual TUI: home/banner (spinning Earth, satellite, stars), credentials, tool selection, installer, output config, run, report screens
- Animated banner: large ORBIT block logo, photo-style spinning Earth with clouds/atmosphere/city lights, orbiting satellite with trail, twinkling stars, shooting stars, live UTC clock
- Secrets management: OS keychain (Windows Credential Manager / macOS Keychain / libsecret) with Fernet AES-256/PBKDF2 fallback; secrets only via child process env vars, masked `***` in all logs
- SHA-256 integrity gate against bundled manifest before any tool launch
- Async subprocess runner for ScubaGear, Maester, Monkey365, ROADtools, Hawk with live streaming logs
- `--dry-run` mode — full TUI and reports from fixture data, no tenant needed
- Parsers: ScubaGear JSON, Maester JSON, Monkey365 JSON/CSV → unified Finding model with cross-tool deduplication
- Scoring matrix: Critical×10 / High×7 / Medium×4 / Low×1, posture score 0–100
- CVE/NIST mapping (8 controls) with bundled offline JSON
- PDF and DOCX executive summary reports with cover, posture score bar, top findings with CVE + remediation, full findings table
- Optional Fernet-encrypted output folder (AES-256, PBKDF2 passphrase)
- Installer screen: ScubaGear/Maester/Monkey365/Hawk via PSGallery, ROADtools via PyPI
- Platform detection: ScubaGear flagged incompatible on non-Windows
- Admin/elevation check with warning banner
- Full documentation: README, TOOLS, PRIVACY, SCORING, INSTALL, VALUE, LEGAL
