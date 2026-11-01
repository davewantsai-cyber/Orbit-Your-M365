# Supported Tools — ORBIT

ORBIT integrates five independent open-source M365 security tools. It calls each through its published command-line interface and does not modify or redistribute any of them.

---

## ScubaGear

**Publisher:** CISA — US Cybersecurity and Infrastructure Security Agency  
**Licence:** CC0 1.0 Universal (public domain dedication)  
**Official source:** https://github.com/cisagov/ScubaGear  
**PSGallery:** https://www.powershellgallery.com/packages/ScubaGear  
**Documentation:** https://cisagov.github.io/ScubaGear/  
**CISA project page:** https://www.cisa.gov/resources-tools/services/secure-cloud-business-applications-scuba-project

### What it checks
ScubaGear assesses a Microsoft 365 tenant against CISA's Secure Cloud Business Applications (SCuBA) Secure Configuration Baselines across six product areas:

| Product | Key controls |
|---------|-------------|
| Microsoft Entra ID (AAD) | MFA, Conditional Access, legacy authentication, privileged roles, identity protection |
| Microsoft Defender | Safe Links, Safe Attachments, anti-phishing policies |
| Exchange Online | Mail flow rules, anti-spam, DKIM/DMARC/SPF, external forwarding |
| SharePoint & OneDrive | External sharing policies, access controls, DLP |
| Microsoft Teams | Meeting security, external access, guest settings |
| Power Platform | DLP policies, connector governance |

### How it works
1. PowerShell queries M365 APIs for configuration settings.
2. Open Policy Agent (OPA) evaluates settings against Rego policy files.
3. Reports are produced as HTML, JSON, and CSV.

### Platform requirements
- **Windows 10/11 or Windows Server 2016+** (Windows only — COM dependencies)
- PowerShell 5.1 or 7.2+
- Global Administrator or equivalent delegated read roles
- App registration with certificate or client secret for non-interactive use

### Install via ORBIT
ORBIT's Installer screen runs `Install-Module -Name ScubaGear` followed by `Initialize-SCuBA` to download the OPA binary.

---

## Maester

**Publisher:** Merill Fernando and open-source community contributors  
**Licence:** MIT  
**Official source:** https://github.com/maester365/maester  
**Website:** https://maester.dev  
**Documentation:** https://maester.dev/docs/

### What it checks
Maester is a Pester-based PowerShell test framework with 280+ tests across five baselines:

| Baseline | Tests | Description |
|----------|-------|-------------|
| CISA SCuBA | 70+ | US CISA Secure Cloud Business Applications baselines |
| CIS M365 | 60+ | CIS Microsoft 365 Foundations Benchmark v3.1.0 |
| EIDSCA | 60+ | Entra ID Security Config Analyser baseline |
| ORCA | Exchange-focused | Office 365 Recommended Configuration Analyser |
| Maester community | 170+ | Best-practice tests curated by the Maester community |

### How it works
Maester runs Pester tests against the Microsoft Graph API and produces a detailed HTML and JSON report.

### Platform requirements
- PowerShell 7 (cross-platform: Windows, macOS, Linux)
- Microsoft Graph read scopes via app registration or Global Reader
- Interactive consent or pre-consented app for automated use

### Install via ORBIT
ORBIT's Installer screen runs `Install-Module -Name Maester`.

---

## Monkey365

**Publisher:** Juan Garrido (silverhack) and contributors  
**Licence:** Apache 2.0  
**Official source:** https://github.com/silverhack/monkey365  
**Documentation:** https://silverhack.github.io/monkey365/

### What it checks
Monkey365 performs configuration reviews of Microsoft 365, Azure subscriptions, and Microsoft Entra ID against industry security benchmarks with 160+ checks:

- CIS Microsoft Azure Foundations Benchmark v3.0.0 and v6.0.0
- CIS Microsoft 365 Foundations Benchmark v3.0.0 and v4.0.0
- Exchange Online, SharePoint, Teams, Entra ID, Azure resources

### How it works
Monkey365 is self-contained — its runtime dependencies are bundled. It collects configuration data through Microsoft APIs, evaluates it against built-in rules, and produces HTML, JSON, and CSV reports with evidence and remediation guidance.

### Platform requirements
- PowerShell 7 (cross-platform)
- App registration with Graph/Exchange read permissions, or delegated admin
- Subscription ID for Azure scope

### Install via ORBIT
ORBIT's Installer screen runs `Install-Module -Name monkey365`.

---

## ROADtools

**Publisher:** Dirk-jan Mollema  
**Licence:** MIT  
**Official source:** https://github.com/dirkjanm/ROADtools  
**PyPI:** https://pypi.org/project/roadrecon/  
**Author blog:** https://dirkjanm.io/

### What it checks
ROADtools is an Entra ID (Azure AD) exploration and enumeration framework. `roadrecon` collects all readable directory data — users, groups, roles, applications, service principals, OAuth2 permissions, conditional access policies — and stores it in a local SQLite database for offline analysis.

ROADtools is primarily a research and investigation tool. ORBIT launches it, collects its output, and stores the results — it is not scored in the current ORBIT posture matrix but provides valuable investigation data.

### Platform requirements
- Python 3.8+, any OS
- Any user account with sign-in capability; reads what that account can read
- Device-code flow supported (no app registration required for basic use)

### Install via ORBIT
ORBIT's Installer screen runs `pip install roadrecon`.

---

## Hawk

**Publisher:** T0pCyber and community contributors  
**Licence:** MIT  
**Official source:** https://github.com/T0pCyber/hawk  
**PSGallery:** https://www.powershellgallery.com/packages/Hawk

### What it checks
Hawk is a PowerShell-based forensic collection tool for Microsoft 365 incident response. It gathers:

- Sign-in histories and audit logs
- Mailbox rules and delegations
- Entra ID role assignments and changes
- OAuth application grants
- Exchange transport rules and forwarding configurations

Hawk is built for post-incident investigation — it collects evidence rather than producing pass/fail policy results. ORBIT launches it and preserves its output; it is not included in the posture score.

### Platform requirements
- PowerShell 7 (cross-platform)
- Exchange/Entra read roles; Global Administrator recommended for complete collection

### Install via ORBIT
ORBIT's Installer screen runs `Install-Module -Name Hawk`.

---

## Related Tools and References

These tools are not integrated into ORBIT but are referenced in documentation and CVE mappings:

| Tool / Resource | Description | Link |
|----------------|-------------|------|
| ORCA | Office 365 Recommended Configuration Analyser (integrated into Maester) | https://github.com/cammurray/orca |
| EIDSCA | Entra ID Security Config Analyser (integrated into Maester) | https://github.com/Cloud-Architekt/AzureAD-Attack-Defense |
| Open Policy Agent | Policy engine used by ScubaGear | https://www.openpolicyagent.org/ |
| Pester | PowerShell test framework used by Maester | https://pester.dev/ |
| Microsoft Graph PowerShell SDK | Graph API access used by several tools | https://learn.microsoft.com/en-us/powershell/microsoftgraph/ |
| CISA SCuBA Baselines | Authoritative M365 security baseline documents | https://github.com/cisagov/ScubaGear/tree/main/baselines |
| CIS Benchmarks | Center for Internet Security M365 benchmarks | https://www.cisecurity.org/benchmark/microsoft_365 |
| NIST SP 800-53 | Security and privacy controls referenced in findings | https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final |
| MITRE ATT&CK Cloud | Threat framework referenced in CVE mappings | https://attack.mitre.org/matrices/enterprise/cloud/ |

---

## Permissions Summary

| Tool | Minimum permissions | Global Admin needed? |
|------|--------------------|--------------------|
| ScubaGear | Global Reader + Exchange/Teams/SP read roles | For interactive consent; can use app-only |
| Maester | Graph read scopes (consented app or Global Reader) | For interactive consent |
| Monkey365 | App registration with Graph/Exchange read, or delegated admin | No (with correct app permissions) |
| ROADtools | Any user with sign-in capability | No |
| Hawk | Exchange/Entra read roles | Recommended for complete collection |

> Always verify the current permission requirements in each tool's official README — they may change between releases.

---

## Parsing Support in ORBIT 1.0

| Tool | Output parsed | Scored | Notes |
|------|--------------|--------|-------|
| ScubaGear | ✓ JSON (`ScubaResults.json`) | ✓ | Full finding model |
| Maester | ✓ JSON report | ✓ | Full finding model |
| Monkey365 | ✓ JSON / CSV (best-effort) | ✓ | Field mapping may vary by version |
| ROADtools | Raw output preserved | ✗ | Investigation data; not scored |
| Hawk | Raw output preserved | ✗ | Forensic collection; not scored |
