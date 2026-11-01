# Changelog

## [1.4.0] — 2026-11-01

### Added
- **Pre-flight check screen** — shown before every run; verifies elevation, PowerShell 7, OPA binary, tool installs, credentials, and output folder writability; all local checks, no network calls; explains why live credential validation is intentionally omitted; Re-check and Proceed buttons
- **Executive Summary PDF** — on-demand 2-page report for non-technical stakeholders: dark cover with posture score bar and risk label (LOW/MEDIUM/HIGH/CRITICAL RISK), priority findings with plain-English remediation, auto-generated summary paragraph; generated async with progress bar, never blocks UI
- **Posture sparkline** — ASCII bar trend (`▁▃▅▇█ 74/100`) on home screen showing last 8 real run scores; dry-run records excluded
- **Remediation action plan** — press `r` or click button in Findings screen; prioritised modal table with control ID, finding, first 80 chars of remediation, CVEs; capped at top 20
- **Keyboard filter in Findings** — press `/` to jump focus to the filter input; live search across all columns
- **Client name on Run screen** — prominent text field at top of Run screen; syncs with Output screen; stamped on all reports
- **Config profile export/import** — `--export-profile FILE` and `--import-profile FILE` CLI flags; portable JSON snapshot of all non-sensitive settings; safe for sharing between machines or team members; never exports secrets
- **Auto-resize launcher** — `launch.py` resizes terminal to 140×43 on macOS (AppleScript + ANSI escape), Windows (`mode con`), and Linux (ANSI) before starting the TUI
- **Slogan** — banner tagline updated to "Orbiting your M365. Nothing escapes."
- **Onboarding re-prompt** — wizard re-shown on every launch until credentials are actually saved; skipping no longer suppresses it permanently

### Improved
- Banner animation reduced from 10fps to 4fps — 60% less CPU, buttons and screen transitions feel instant
- Installer screen redesigned: compact one-row-per-tool layout with status badge, version, Install/Update/Remove per tool; fits on one screen with no scroll; log expands on use
- Quotes panel uses `1fr` height — fills all available space between fixed sections rather than fixed 6 rows
- `#last-run` now shows "Pending first run — no score determined yet." when no real runs recorded; dry-run records excluded from history display and sparkline
- Terminal size warning threshold updated to 120×40

### Tests
- 77 passing (unchanged — new features are UI/async, covered by existing integration tests)

---

## [1.3.0] — 2026-11-01

### Added
- Help screen (`?` key) — full-screen reference overlay: shortcuts, tool list, requirements, privacy note
- Onboarding wizard — shown on first launch only, skippable at any step; guides through credentials and tool selection
- Findings viewer screen — sortable/filterable DataTable with severity colour coding; row detail modal with CVEs and remediation
- Run comparison / delta — compare any two history entries; shows score delta, severity deltas, issues resolved
- Auto-update checker — silent background check against GitHub releases API; dim notice in home screen if newer version available
- Terminal size warning — shown if terminal is under 100×32; "Continue anyway" option
- `--list-tools` CLI flag — prints tool status table to stdout and exits, no TUI needed
- GitHub Pages landing page (`docs/index.html`) — dark-themed, ASCII logo, feature cards, tools table, install block, privacy strip
- vhs demo recording script (`demo.tape`) — record animated GIF of the TUI

### Improved
- Run screen now uses `RichLog` with 2000-line buffer and user-scrollable history
- Report filenames now include client name slug and date: `ORBIT_Summary_Acme_Ltd_2026-11-01.pdf`
- `pyproject.toml` entry point added — `orbit` works as a CLI command after `pip install -e .`

### Tests
- 58 → 77 passing

---

## [1.2.0] — 2026-11-01

### Added
- Logged-in username and permission level (Administrator / Standard User) displayed in banner — green when elevated, amber when not
- Rotating quotes panel filling empty space on home screen — 38 quotes across cybersecurity, open source, hacking, and privacy; fades in/out with attribution

### Improved
- Banner tick rate reduced to 100ms (10fps) — smoother on lower-end hardware
- Quotes widget tick rate reduced to 150ms (6fps) — lower CPU, visually identical
- Nav buttons now fill full terminal width with `min-width: 0` and `overflow: hidden hidden` — no clipping at any terminal size
- Info panel columns use fractional widths — dashboard scales with terminal width
- Quotes widget given fixed 6-row height to guarantee visibility at all terminal sizes

### Fixed
- Worker thread context error (`LookupError: active_app`) — reverted to synchronous dashboard refresh which is stable across Textual versions

---

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
