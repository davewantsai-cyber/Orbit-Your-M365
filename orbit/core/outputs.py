"""Output folder creation and post-run packaging."""
from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from orbit.security.encryption import encrypt_folder

FORMATS = ("HTML", "JSON", "CSV", "PDF", "DOCX")


@dataclass
class OutputConfig:
    base_dir: Path = field(default_factory=lambda: Path("output"))
    formats: set[str] = field(default_factory=lambda: {"JSON", "PDF", "DOCX"})
    encrypt: bool = False
    keep_unencrypted: bool = True


def make_run_folder(base: Path, now: datetime | None = None) -> Path:
    now = now or datetime.now()
    folder = Path(base) / f"{now:%Y-%m-%d_%H-%M}"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def package(folder: Path, cfg: OutputConfig, passphrase: str | None,
            iterations: int | None = None) -> Path | None:
    """Encrypt the folder to ZIP if requested; remove plaintext unless keep_unencrypted."""
    if not cfg.encrypt:
        return None
    if not passphrase:
        raise ValueError("A passphrase is required for encrypted output")
    kw = {"iterations": iterations} if iterations else {}
    archive = encrypt_folder(folder, passphrase, **kw)
    if not cfg.keep_unencrypted and archive.exists():
        shutil.rmtree(folder)
    return archive
