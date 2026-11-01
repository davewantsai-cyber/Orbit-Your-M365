# Changelog

## 1.0.0
- Textual TUI: home/banner/clock, credentials, tool selection, installer, output, run, report screens.
- Secrets in OS keychain with Fernet/PBKDF2 fallback; secrets only via child env vars, masked in logs.
- SHA-256 integrity gate before tool launch.
- Async runner for ScubaGear, Maester, Monkey365, ROADtools, Hawk; `--dry-run` fixture playback.
- Parsers (ScubaGear, Maester, Monkey365), cross-tool dedupe, scoring, CVE/NIST map.
- PDF and DOCX summary reports; optional encrypted ZIP output.
