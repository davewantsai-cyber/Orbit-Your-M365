"""Fernet (AES) encryption with PBKDF2-HMAC-SHA256 key derivation, plus folder -> ZIP."""
from __future__ import annotations

import base64
import io
import os
import zipfile
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

ITERATIONS = 600_000
SALT_LEN = 16
MAGIC = b"ORBT1"


class DecryptionError(Exception):
    pass


def derive_key(passphrase: str, salt: bytes, iterations: int = ITERATIONS) -> bytes:
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=iterations)
    return base64.urlsafe_b64encode(kdf.derive(passphrase.encode("utf-8")))


def encrypt_bytes(data: bytes, passphrase: str, iterations: int = ITERATIONS) -> bytes:
    """Return MAGIC + salt + Fernet token."""
    salt = os.urandom(SALT_LEN)
    token = Fernet(derive_key(passphrase, salt, iterations)).encrypt(data)
    return MAGIC + salt + token


def decrypt_bytes(blob: bytes, passphrase: str, iterations: int = ITERATIONS) -> bytes:
    if not blob.startswith(MAGIC):
        raise DecryptionError("Not an ORBIT encrypted blob")
    salt = blob[len(MAGIC): len(MAGIC) + SALT_LEN]
    token = blob[len(MAGIC) + SALT_LEN:]
    try:
        return Fernet(derive_key(passphrase, salt, iterations)).decrypt(token)
    except InvalidToken as exc:
        raise DecryptionError("Wrong passphrase or corrupted data") from exc


def zip_folder_bytes(folder: Path) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in sorted(folder.rglob("*")):
            if p.is_file():
                zf.write(p, p.relative_to(folder).as_posix())
    return buf.getvalue()


def encrypt_folder(folder: Path, passphrase: str, dest: Path | None = None,
                   iterations: int = ITERATIONS) -> Path:
    """Zip a folder and Fernet-encrypt the archive. Returns the path of the .orbit.zip file."""
    dest = dest or folder.with_name(folder.name + ".orbit.zip")
    dest.write_bytes(encrypt_bytes(zip_folder_bytes(folder), passphrase, iterations))
    return dest


def decrypt_archive(archive: Path, passphrase: str, out_dir: Path,
                    iterations: int = ITERATIONS) -> None:
    data = decrypt_bytes(archive.read_bytes(), passphrase, iterations)
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        zf.extractall(out_dir)
