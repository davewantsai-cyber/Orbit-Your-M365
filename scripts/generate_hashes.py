#!/usr/bin/env python3
"""Populate data/tool_hashes.json with SHA-256 hashes of installed tools.

Run once after installing tools, and again after any update:

    python scripts/generate_hashes.py

Each installed tool's directory is scanned, every file is hashed, and the
results are merged into data/tool_hashes.json under the tool's current version.
Existing entries for other versions are preserved.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "data" / "tool_hashes.json"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def hash_dir(root: Path) -> dict[str, str]:
    return {
        p.relative_to(root).as_posix(): sha256(p)
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }


def run(cmd: list[str]) -> str:
    try:
        return subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return ""


def ps(script: str) -> str:
    pwsh = shutil.which("pwsh") or shutil.which("powershell")
    if not pwsh:
        return ""
    return run([pwsh, "-NonInteractive", "-NoProfile", "-Command", script])


# ---------------------------------------------------------------------------
# Per-tool discovery
# ---------------------------------------------------------------------------

def find_ps_module(name: str) -> tuple[str | None, Path | None]:
    """Return (version, install_dir) for a PowerShell module, or (None, None)."""
    out = ps(
        f"$m = Get-Module -ListAvailable -Name {name} | "
        f"Sort-Object Version -Descending | Select-Object -First 1; "
        f"if ($m) {{ \"$($m.Version)|$($m.ModuleBase)\" }}"
    )
    if "|" not in out:
        return None, None
    ver, path = out.split("|", 1)
    p = Path(path.strip())
    return ver.strip(), p if p.is_dir() else None


def find_roadrecon() -> tuple[str | None, Path | None]:
    """Return (version, site-packages dir) for roadrecon."""
    out = run([sys.executable, "-c",
               "import importlib.metadata, pathlib; "
               "d = importlib.metadata.distribution('roadrecon'); "
               "print(d.metadata['Version'] + '|' + str(d.locate_file('.')))"])
    if "|" not in out:
        return None, None
    ver, path = out.split("|", 1)
    p = Path(path.strip()) / "roadrecon"
    return ver.strip(), p if p.is_dir() else None


TOOL_FINDERS = {
    "scubagear":  lambda: find_ps_module("ScubaGear"),
    "maester":    lambda: find_ps_module("Maester"),
    "monkey365":  lambda: find_ps_module("monkey365"),
    "hawk":       lambda: find_ps_module("Hawk"),
    "roadtools":  find_roadrecon,
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    if MANIFEST.exists():
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    else:
        manifest = {"schema": 1, "tools": {}}

    tools_section: dict = manifest.setdefault("tools", {})
    any_found = False

    for tool_name, finder in TOOL_FINDERS.items():
        tool_entry: dict = tools_section.setdefault(tool_name, {"versions": {}})
        versions: dict = tool_entry.setdefault("versions", {})

        print(f"Scanning {tool_name} ...", end=" ", flush=True)
        version, install_dir = finder()

        if version is None or install_dir is None:
            print("not installed — skipped")
            continue

        print(f"v{version} at {install_dir} ...", end=" ", flush=True)
        files = hash_dir(install_dir)
        versions[version] = {"install_dir": str(install_dir), "files": files}
        print(f"✓ {len(files)} files hashed")
        any_found = True

    if not any_found:
        print(
            "\nNo tools found. Install tools first (use ORBIT's Installer screen or\n"
            "see docs/INSTALL.md), then re-run this script.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Remove legacy _note if present (replaced by README docs)
    manifest.pop("_note", None)

    MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"\nManifest written to {MANIFEST.relative_to(ROOT)}")
    print("Re-run this script any time you install or update a tool.")


if __name__ == "__main__":
    main()
