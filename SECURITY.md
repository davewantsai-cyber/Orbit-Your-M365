# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.0.x   | ✅ Yes    |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

If you discover a security vulnerability in ORBIT — including issues with credential storage, encryption, privilege escalation, or dependency vulnerabilities — please report it privately:

**Email:** open an issue marked `[SECURITY]` with minimal detail and I will respond within 48 hours with a private channel to share the full details.

Or use GitHub's built-in private vulnerability reporting:  
**[Report a vulnerability](../../security/advisories/new)**

Please include:
- A description of the vulnerability
- Steps to reproduce
- Potential impact
- Any suggested fixes (if you have them)

I will acknowledge receipt within 48 hours and aim to release a fix within 14 days for critical issues.

## Scope

ORBIT itself does not make network connections — vulnerabilities in the tools it launches (ScubaGear, Maester, etc.) should be reported to their respective maintainers:

| Tool | Report to |
|------|-----------|
| ScubaGear | https://github.com/cisagov/ScubaGear/security |
| Maester | https://github.com/maester365/maester/issues |
| Monkey365 | https://github.com/silverhack/monkey365/issues |
| ROADtools | https://github.com/dirkjanm/ROADtools/issues |
| Hawk | https://github.com/T0pCyber/hawk/issues |

## Credential Safety Reminder

ORBIT stores credentials in your OS keychain. If you believe your M365 credentials have been compromised, rotate them in the Microsoft Entra admin centre immediately — do not wait for an ORBIT update.
