# Contributing to ORBIT

Thanks for your interest. ORBIT is a small personal project — contributions are welcome but please read this first.

## Before opening a PR

- **Open an issue first** for anything beyond a small bug fix. This avoids wasted effort if the change isn't a good fit.
- Keep PRs focused on one thing. Mixed-purpose PRs take much longer to review.
- All contributions must respect the project's core principles:
  - No outbound network connections from ORBIT itself
  - No telemetry or analytics of any kind
  - No plaintext secrets anywhere in code, logs, or config files
  - No dependencies that phone home

## Setup

```bash
git clone https://github.com/OpenSourceByReece/Orbit365.git
cd Orbit365
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

## Running tests

```bash
pytest tests/ -v
```

All 36 tests must pass. If you add a feature, add tests for it.

## Linting

```bash
ruff check .
ruff format .
```

Fix all ruff errors before submitting. The CI pipeline will block on lint failures.

## What's welcome

- Bug fixes with a test that proves the bug existed
- Expanded CVE / remediation mappings in `data/cve_mappings.json`
- Improved documentation and installation guides
- New tool adapters (must follow the `Tool` base class in `orbit/core/tools/base.py`)
- Platform-specific improvements (Linux keychain, Windows-specific UX)
- Dry-run fixture improvements

## What won't be merged

- Telemetry, analytics, crash reporting, or update checks
- Dependencies that make outbound connections from ORBIT's own code
- Plaintext credential storage of any kind
- Features that require paid services or API keys to use
- Large scope expansions without prior discussion

## Code style

- Python 3.10+ compatible
- Type hints on all public functions and methods
- Docstrings on all modules and classes
- Follow existing patterns — check a neighbouring file before introducing a new abstraction
- No wildcard imports

## Commit messages

Plain English, present tense, imperative mood:
- `fix: handle missing keyring on headless Linux`
- `feat: add client name field to output config`
- `docs: add Maester permission details`

## Licence

By submitting a PR you agree that your contribution is licensed under the MIT licence.
