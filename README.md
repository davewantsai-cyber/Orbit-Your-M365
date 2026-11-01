# ORBIT — Office 365 Risk & Baseline Intelligence Toolkit

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey?style=flat-square" alt="Platform">
  <img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="MIT License">
  <img src="https://img.shields.io/badge/version-1.2.0-purple?style=flat-square" alt="Version 1.2.0">
  <img src="https://img.shields.io/badge/telemetry-none-brightgreen?style=flat-square" alt="No telemetry">
  <img src="https://img.shields.io/badge/client--side-100%25-brightgreen?style=flat-square" alt="Client-side">
</p>

```
 ██████╗ ██████╗ ██████╗ ██╗████████╗
██╔═══██╗██╔══██╗██╔══██╗██║╚══██╔══╝
██║   ██║██████╔╝██████╔╝██║   ██║
██║   ██║██╔══██╗██╔══██╗██║   ██║
╚██████╔╝██║  ██║████████╗██║   ██║
 ╚═════╝ ╚═╝  ╚═╝╚═══════╝╚═╝   ╚═╝

  Office 365 Risk & Baseline Intelligence Toolkit
  Author  : Reece Gabriel Dickson
  Role    : Independent Cybersecurity Research Analyst
  Version : v1.2.0
```

ORBIT is a **terminal application** with an animated TUI that orchestrates leading M365 security auditing tools, manages their credentials securely, runs them, normalises and scores every finding, and writes a **PDF / DOCX executive summary report** — all without your data ever leaving your machine.

What normally takes a skilled analyst **4–8 hours** of manual portal work and report-writing, ORBIT compresses to **10–15 minutes** of hands-on time.

---

## Contents

- [What ORBIT Does](#what-orbit-does)
- [Tools Integrated](#tools-integrated)
- [Quickstart](#quickstart)
- [Installation](#installation)
- [How to Test Without a Work Tenant](#how-to-test-without-a-work-tenant)
- [Usage Walkthrough](#usage-walkthrough)
- [Output and Reports](#output-and-reports)
- [Scoring Methodology](#scoring-methodology)
- [Architecture](#architecture)
- [Security and Privacy](#security-and-privacy)
- [Credits and Acknowledgements](#credits-and-acknowledgements)
- [Legal Notices](#legal-notices)
- [Contributing](#contributing)

---

## What ORBIT Does

1. **Checks your environment** — admin rights, PowerShell version, OS compatibility — before anything runs.
2. **Stores credentials securely** — Tenant ID, App ID, and client secrets go into your OS keychain (Windows Credential Manager / macOS Keychain / libsecret). Never written in plaintext. Never in process arguments visible to `ps`.
3. **Verifies tool integrity** — SHA-256 hash check against a bundled manifest before any tool is launched. A mismatch is a hard stop.
4. **Installs / updates tools** — one screen to install ScubaGear, Maester, Monkey365, ROADtools, and Hawk from their official sources.
5. **Runs selected tools** — async subprocess launcher with live streaming logs and per-tool progress. Tools are stopped cleanly on cancel.
6. **Parses and normalises output** — JSON and CSV from ScubaGear, Maester, and Monkey365 unified into a single `Finding` model with severity, control ID, CVE references, and remediation text.
7. **Scores findings** — a weighted risk matrix (Critical ×10 / High ×7 / Medium ×4 / Low ×1) produces an overall posture score and ranked top findings.
8. **Generates a summary report** — PDF or DOCX with cover page, posture score bar, top 2–3 critical findings with CVE + remediation steps, and a full findings table. The native tool reports are preserved alongside it in the output folder.
9. **Optionally encrypts output** — Fernet (AES-256) with a PBKDF2 passphrase. An unencrypted copy can be saved as well.

---

## Tools Integrated

ORBIT integrates the following independent, open-source security tools. ORBIT does not modify, fork, or redistribute any of them — it calls them through their published interfaces.

| Tool | Coverage | Language | Official Source |
|------|----------|----------|-----------------|
| **ScubaGear** | CISA SCuBA baselines: Entra ID, Defender, Exchange Online, SharePoint/OneDrive, Teams, Power Platform | PowerShell | [github.com/cisagov/ScubaGear](https://github.com/cisagov/ScubaGear) |
| **Maester** | Pester test framework: CISA SCuBA, CIS M365, ORCA, EIDSCA (280+ tests) | PowerShell | [maester.dev](https://maester.dev) · [github.com/maester365/maester](https://github.com/maester365/maester) |
| **Monkey365** | M365, Azure, Entra ID config review against CIS benchmarks (160+ checks) | PowerShell | [github.com/silverhack/monkey365](https://github.com/silverhack/monkey365) |
| **ROADtools** | Entra ID enumeration and offline analysis (users, roles, apps, policies) | Python | [github.com/dirkjanm/ROADtools](https://github.com/dirkjanm/ROADtools) |
| **Hawk** | Exchange Online / Entra ID forensic collection for IR and investigation | PowerShell | [github.com/T0pCyber/hawk](https://github.com/T0pCyber/hawk) |

Further reading and reference tools:
- [CISA SCuBA Project](https://www.cisa.gov/resources-tools/services/secure-cloud-business-applications-scuba-project) — the authoritative source for Microsoft 365 secure configuration baselines
- [Open Policy Agent (OPA)](https://www.openpolicyagent.org/) — policy engine used internally by ScubaGear
- [ORCA](https://github.com/cammurray/orca) — Office 365 Recommended Configuration Analyser (integrated via Maester)
- [EIDSCA](https://github.com/Cloud-Architekt/AzureAD-Attack-Defense/blob/main/AADSecurityConfigAnalyzer.md) — Entra ID Security Config Analyser (integrated via Maester)
- [Pester](https://pester.dev/) — PowerShell test framework that Maester is built on

---

## Quickstart

```bash
# Clone
git clone https://github.com/OpenSourceByReece/Orbit365.git
cd orbit-m365

# Create venv and install
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

# Run tests (no tenant needed)
pytest tests/ -v

# Launch in dry-run mode (full TUI, no M365 tenant needed)
python orbit.py --dry-run

# Real run (see Installation for prerequisites)
python orbit.py
```

---

## Installation

### Windows 10/11 (Primary Platform)

> **ScubaGear requires Windows.** All other tools work cross-platform.

1. Install **Python 3.10+** from [python.org](https://www.python.org/downloads/) — tick "Add to PATH".
2. Install **PowerShell 7**: `winget install Microsoft.PowerShell`
3. In the project folder:
   ```powershell
   python -m venv .venv
   .venv\Scripts\activate
   pip install -e ".[dev]"
   ```
4. Open **PowerShell 7 as Administrator** (required for ScubaGear/Maester).
5. Run `python orbit.py` and use the **Installer** screen to install each tool.
6. Enter your credentials in the **Credentials** screen, select tools, configure output, then **Run**.

### macOS

```bash
brew install python@3.12
brew install powershell          # optional — needed for PS-based tools
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python orbit.py --dry-run
```

ScubaGear shows as "incompatible OS" on macOS — this is expected. Maester, Monkey365, ROADtools, and Hawk all work on macOS with PowerShell 7.

### Linux

```bash
# Install PowerShell 7 (Microsoft's package repo)
# https://learn.microsoft.com/en-us/powershell/scripting/install/installing-powershell-on-linux
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python orbit.py --dry-run
```

### Verify

```bash
pytest tests/ -v          # 36 tests, all should pass
python orbit.py --help
```

See [docs/INSTALL.md](docs/INSTALL.md) for detailed step-by-step instructions.

---

## How to Test Without a Work Tenant

You don't need a production M365 tenant to use or test ORBIT.

### Option 1 — Dry-run mode (no tenant at all)

```bash
python orbit.py --dry-run
```

Plays back fixture JSON instead of running real tools. The full TUI, scoring engine, and report generation all work. Reports are labelled `(DRY RUN)`. Use this to explore the UI, demo to a client, or run in CI.

### Option 2 — Microsoft 365 E5 30-day free trial

Sign up at [microsoft.com/microsoft-365/enterprise/e5](https://www.microsoft.com/en-gb/microsoft-365/enterprise/e5) using a **throwaway Outlook/Hotmail account**. No credit card required for the trial. You get:
- 25 user licences, full E5 feature set (Entra ID P2, Defender, Purview, Exchange, Teams)
- 30 days — enough for a full build-and-test cycle

Deliberately misconfigure the sandbox (disable MFA for some users, enable legacy auth, weaken Conditional Access) to create real findings and verify ORBIT catches them.

### Option 3 — Microsoft 365 Developer Program sandbox (E5, 90-day auto-renew)

Sign up at [developer.microsoft.com/en-us/microsoft-365/dev-program](https://developer.microsoft.com/en-us/microsoft-365/dev-program). Gets you a full E5 sandbox with 25 pre-populated users that auto-renews every 90 days as long as you actively use it.

> **Note:** As of 2023, Microsoft requires a Visual Studio Professional/Enterprise subscription or partner programme membership to qualify.

### Option 4 — Unit tests (no tenant, no tool install)

```bash
pytest tests/ -v
```

~80% of the codebase — secrets, scoring, parsers, report generation, hash checks — is tested entirely with golden fixture JSON. No network connection needed.

---

## Usage Walkthrough

### Screen 1 — Home

On launch, ORBIT shows:
- An animated banner with a spinning ASCII Earth, satellite, and star field
- Tool status dashboard: installed ✓ / not installed ✗ / update available ↑ / incompatible OS ⚠
- Admin / elevation status with a warning if not running as Administrator
- System info: OS, PowerShell version

### Screen 2 — Credentials

Enter connection details for each tool you want to use. Values are stored in your OS keychain immediately on save — never on disk in plaintext.

| Tool | Required credentials |
|------|---------------------|
| ScubaGear / Maester | Tenant ID, App (Client) ID, Certificate thumbprint or Client Secret |
| Monkey365 | Tenant ID, App ID, Client Secret, Subscription ID (for Azure scope) |
| ROADtools | Client ID; device-code flow available |
| Hawk | Global Admin UPN |

### Screen 3 — Tools

Checkbox list to select which tools to run. Incompatible tools (wrong OS) and tools with missing credentials are flagged inline.

### Screen 4 — Output

- Choose an output directory (a timestamped subfolder is created automatically: `output/2026-11-01_14-32/`)
- Select report formats: HTML, JSON, CSV (native tool formats), PDF, DOCX (ORBIT summary)
- Optionally encrypt the output folder to an AES-256 ZIP with a passphrase
- Option to save an unencrypted copy alongside the encrypted one

### Screen 5 — Installer

Install or update any tool from its official source:
- ScubaGear, Maester, Monkey365, Hawk → PowerShell Gallery (`Install-Module`)
- ROADtools → PyPI (`pip install roadrecon`)
- OPA binary → fetched by ScubaGear's own `Initialize-SCuBA`

Shows current vs. latest version, install progress, and live log output.

### Screen 6 — Run

- Each tool runs as an async subprocess with live streaming log output
- Per-tool status: Pending → Running → Complete ✓ / Failed ✗ / Skipped
- Stop individual tools or cancel all
- Credentials injected as environment variables only — never in process arguments

### Screen 7 — Report

View the generated summary and open the output folder. The ORBIT summary report contains:
1. Cover page: client name placeholder, date, assessor, tools used
2. Overall posture score (0–100) with severity breakdown
3. Top 2–3 critical/high findings with CVE references and remediation steps
4. Full findings table: ID, severity, title, source tool, control reference
5. Footer: "Generated by ORBIT v1.0.0 — All processing client-side. No data transmitted."

---

## Output and Reports

```
output/
└── 2026-11-01_14-32/
    ├── ORBIT_Summary.pdf          ← ORBIT executive summary
    ├── ORBIT_Summary.docx         ← same content as Word document
    ├── ScubaGear/
    │   ├── ScubaResults.html
    │   ├── ScubaResults.json
    │   └── ScubaResults.csv
    ├── Maester/
    │   └── MaesterReport.json
    └── Monkey365/
        └── Monkey365Report.json
```

The raw tool reports are preserved exactly as the tool produces them. ORBIT's summary is additive — it never modifies tool output.

---

## Scoring Methodology

See [docs/SCORING.md](docs/SCORING.md) for full details.

| Severity | Weight | Colour |
|----------|--------|--------|
| Critical | 10 | 🔴 Red |
| High | 7 | 🟠 Orange |
| Medium | 4 | 🟡 Yellow |
| Low | 1 | 🟢 Green |
| Pass | 0 | — |

**Posture score** = `(passed_controls / total_controls) × 100`

CVE references are looked up from a bundled static JSON (`data/cve_mappings.json`) keyed on M365 control IDs. No external network calls are made for CVE data.

---

## Architecture

```
orbit-m365/
├── orbit.py                  ← entry point
├── orbit/
│   ├── config.py             ← AUTHOR, VERSION, YEAR constants
│   ├── tui/                  ← Textual screens and widgets
│   ├── core/
│   │   ├── secrets.py        ← keyring + Fernet fallback
│   │   ├── hash_checker.py   ← SHA-256 integrity gate
│   │   ├── runner.py         ← async subprocess launcher
│   │   └── tools/            ← one adapter per tool
│   ├── reporting/            ← parser, scorer, PDF, DOCX
│   └── security/             ← folder encryption
├── data/
│   ├── cve_mappings.json     ← bundled CVE reference (offline)
│   └── tool_hashes.json      ← known-good tool hashes
├── tests/
│   └── fixtures/             ← anonymised sample tool output
└── docs/
```

**Stack:** Python 3.10+, [Textual](https://textual.textualize.io/), [Rich](https://github.com/Textualize/rich), [keyring](https://github.com/jaraco/keyring), [cryptography](https://cryptography.io/), [fpdf2](https://py-pdf.github.io/fpdf2/), [python-docx](https://python-docx.readthedocs.io/), [Jinja2](https://jinja.palletsprojects.com/), [click](https://click.palletsprojects.com/).

---

## Security and Privacy

See [docs/PRIVACY.md](docs/PRIVACY.md) for the full statement.

**Short version:**
- ORBIT makes **no outbound network connections** of its own.
- Secrets are stored in your **OS keychain** (Windows Credential Manager / macOS Keychain / libsecret). The Fernet-encrypted fallback (`~/.orbit/secrets.enc`) is used only if no keychain is available.
- Secrets are **never** written to plaintext files, logs, or process arguments.
- There is **no telemetry, analytics, or update checking**.
- All CVE lookups use a **bundled offline JSON file**.
- Output can be **AES-256 encrypted** at rest.

---

## Credits and Acknowledgements

ORBIT is a launcher and orchestration layer. All security assessment capability comes from the independent tools listed below. Their authors deserve full credit.

| Tool | Author / Maintainer | Licence |
|------|---------------------|---------|
| [ScubaGear](https://github.com/cisagov/ScubaGear) | [CISA](https://www.cisa.gov/) | CC0 1.0 Universal |
| [Maester](https://github.com/maester365/maester) | [Merill Fernando](https://github.com/merill) and community contributors | MIT |
| [Monkey365](https://github.com/silverhack/monkey365) | [Juan Garrido (silverhack)](https://github.com/silverhack) | Apache 2.0 |
| [ROADtools](https://github.com/dirkjanm/ROADtools) | [Dirk-jan Mollema](https://github.com/dirkjanm) | MIT |
| [Hawk](https://github.com/T0pCyber/hawk) | [T0pCyber](https://github.com/T0pCyber) and community | MIT |
| [ORCA](https://github.com/cammurray/orca) | [Cam Murray](https://github.com/cammurray) | MIT (integrated via Maester) |
| [EIDSCA](https://github.com/Cloud-Architekt/AzureAD-Attack-Defense) | [Thomas Naunheim](https://github.com/Cloud-Architekt) and contributors | MIT (integrated via Maester) |
| [Open Policy Agent](https://www.openpolicyagent.org/) | [CNCF / OPA Community](https://github.com/open-policy-agent/opa) | Apache 2.0 (used by ScubaGear) |
| [Pester](https://pester.dev/) | [Jakub Jareš](https://github.com/nohwnd) and contributors | Apache 2.0 (used by Maester) |

**Python libraries:**

| Library | Author | Licence |
|---------|--------|---------|
| [Textual](https://github.com/Textualize/rich) | Textualize | MIT |
| [Rich](https://github.com/Textualize/rich) | Will McGugan / Textualize | MIT |
| [keyring](https://github.com/jaraco/keyring) | Jason R. Coombs | MIT |
| [cryptography](https://cryptography.io/) | PyCA | Apache 2.0 / BSD |
| [fpdf2](https://py-pdf.github.io/fpdf2/) | PyFPDF contributors | LGPL 3.0 |
| [python-docx](https://python-docx.readthedocs.io/) | Steve Canny | MIT |
| [Jinja2](https://jinja.palletsprojects.com/) | Armin Ronacher / Pallets | BSD |
| [click](https://click.palletsprojects.com/) | Pallets | BSD |

Reference documentation and standards:
- [CISA Secure Cloud Business Applications (SCuBA) Project](https://www.cisa.gov/resources-tools/services/secure-cloud-business-applications-scuba-project)
- [CISA SCuBA M365 Secure Configuration Baselines](https://github.com/cisagov/ScubaGear/tree/main/baselines)
- [CIS Microsoft 365 Foundations Benchmark](https://www.cisecurity.org/benchmark/microsoft_365)
- [NIST SP 800-53 Security Controls](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final)
- [MITRE ATT&CK for Cloud](https://attack.mitre.org/matrices/enterprise/cloud/)

---

## Legal Notices

See [LEGAL.md](LEGAL.md) for the complete legal notice including fair use, disclaimer of liability, and privacy statement.

**Summary:**

> ORBIT is provided as a personal, research, and educational tool under the MIT licence. Use it only against Microsoft 365 tenants you own or have written authorisation to assess. The author accepts no liability for misuse, data loss, or security incidents arising from use of this software or the tools it launches. All integrated tool names, trademarks, and logos belong to their respective owners.

---

## Contributing

Issues and pull requests are welcome. Please:
- Open an issue before starting significant work
- Keep PRs focused on a single change
- Run `pytest tests/ -v` and `ruff check .` before submitting
- Do not add telemetry, remote calls from ORBIT itself, or hardcoded credentials of any kind

---

## Author

**Reece Gabriel Dickson**  
Independent Cybersecurity Research Analyst  
[github.com/OpenSourceByReece](https://github.com/OpenSourceByReece)

---

*Only run ORBIT and the tools it launches against Microsoft 365 tenants you own or have explicit written authorisation to assess.*
