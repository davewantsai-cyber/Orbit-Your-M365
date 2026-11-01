"""SHA-256 integrity checks of installed tool files against data/tool_hashes.json."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from orbit.config import DATA_DIR

MANIFEST_PATH = DATA_DIR / "tool_hashes.json"


class HashStatus(str, Enum):
    OK = "ok"
    MISMATCH = "mismatch"
    UNVERIFIED = "unverified"  # no manifest entry for this tool/version


@dataclass
class HashResult:
    tool: str
    version: str | None
    status: HashStatus
    mismatches: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)

    @property
    def blocks_run(self) -> bool:
        return self.status is HashStatus.MISMATCH

    def explain(self) -> str:
        if self.status is HashStatus.OK:
            return f"{self.tool} {self.version}: all file hashes match the manifest."
        if self.status is HashStatus.UNVERIFIED:
            return f"{self.tool} {self.version}: no manifest entry; integrity could not be verified."
        bad = ", ".join(self.mismatches + [f"{m} (missing)" for m in self.missing])
        return (f"{self.tool} {self.version}: integrity check FAILED for: {bad}. "
                "The installed files differ from the trusted manifest and may be tampered with "
                "or from an unexpected release.")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def hash_tree(root: Path) -> dict[str, str]:
    return {p.relative_to(root).as_posix(): sha256_file(p)
            for p in sorted(root.rglob("*")) if p.is_file()}


def load_manifest(path: Path = MANIFEST_PATH) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def check_tool(tool: str, version: str | None, install_dir: Path | None,
               manifest: dict | None = None) -> HashResult:
    manifest = manifest if manifest is not None else load_manifest()
    files = (manifest.get("tools", {}).get(tool, {}).get("versions", {})
             .get(version or "", {}).get("files"))
    if not files or install_dir is None:
        return HashResult(tool, version, HashStatus.UNVERIFIED)
    mismatches, missing = [], []
    for rel, expected in files.items():
        p = Path(install_dir) / rel
        if not p.is_file():
            missing.append(rel)
        elif sha256_file(p).lower() != expected.lower():
            mismatches.append(rel)
    status = HashStatus.MISMATCH if (mismatches or missing) else HashStatus.OK
    return HashResult(tool, version, status, mismatches, missing)


def gate_run(results: list[HashResult], override: bool = False) -> tuple[bool, str]:
    """Hard stop on any mismatch unless the user explicitly overrides."""
    bad = [r for r in results if r.blocks_run]
    if not bad:
        return True, ""
    msg = "\n".join(r.explain() for r in bad)
    return (override, msg)
