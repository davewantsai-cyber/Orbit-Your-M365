# AGENTS.md
ORBIT - M365 security audit orchestrator (Textual TUI). Full spec: `KICKOFF.md`.
- Scope is milestones M0-M10 only; do not expand.
- Secrets never in args, logs, or plaintext on disk. No network calls from ORBIT itself.
- Setup: `uv venv && uv pip install -e ".[dev]"`; test: `pytest tests/ -v`.
- Dry-run: `python orbit.py --dry-run` plays back `tests/fixtures/`.
