import json

import pytest

from orbit.core.secrets import MASK, SecretStore, redact
from orbit.security.encryption import (
    DecryptionError,
    decrypt_archive,
    decrypt_bytes,
    encrypt_bytes,
    encrypt_folder,
)

FAST = 1000  # PBKDF2 iterations for fast tests
SECRET = "s3cr3t-VALUE-xyz"


def test_bytes_round_trip():
    blob = encrypt_bytes(b"hello", "pw", iterations=FAST)
    assert b"hello" not in blob
    assert decrypt_bytes(blob, "pw", iterations=FAST) == b"hello"


def test_wrong_passphrase():
    blob = encrypt_bytes(b"hello", "pw", iterations=FAST)
    with pytest.raises(DecryptionError):
        decrypt_bytes(blob, "nope", iterations=FAST)


def test_store_round_trip_and_no_plaintext(tmp_path):
    path = tmp_path / "secrets.enc"
    store = SecretStore("pw", path, use_keyring=False, iterations=FAST)
    store.save("monkey365", {"tenant_id": "t", "client_secret": SECRET})
    assert store.load("monkey365")["client_secret"] == SECRET
    raw = path.read_bytes()
    assert SECRET.encode() not in raw and b"client_secret" not in raw
    # nothing else in tmp dir holds the secret
    for p in tmp_path.rglob("*"):
        if p.is_file():
            assert SECRET.encode() not in p.read_bytes()


def test_store_requires_passphrase(tmp_path):
    store = SecretStore(None, tmp_path / "s.enc", use_keyring=False, iterations=FAST)
    with pytest.raises(PermissionError):
        store.save("hawk", {"admin_upn": "a@b"})


def test_masking_and_redaction(tmp_path):
    store = SecretStore("pw", tmp_path / "s.enc", use_keyring=False, iterations=FAST)
    store.save("scubagear", {"tenant_id": "t", "client_secret": SECRET})
    assert store.masked("scubagear")["client_secret"] == MASK
    assert store.masked("scubagear")["tenant_id"] == "t"
    assert SECRET not in json.dumps(store.masked("scubagear"))
    assert SECRET not in redact(f"auth with {SECRET} ok", store.secret_values("scubagear"))


def test_keyring_path(monkeypatch):
    mem: dict = {}
    import keyring

    monkeypatch.setattr(keyring, "set_password", lambda s, k, v: mem.__setitem__((s, k), v))
    monkeypatch.setattr(keyring, "get_password", lambda s, k: mem.get((s, k)))
    store = SecretStore(use_keyring=True)
    store.save("hawk", {"admin_upn": "x@y.z"})
    assert store.load("hawk") == {"admin_upn": "x@y.z"}


def test_encrypt_folder_round_trip(tmp_path):
    src = tmp_path / "out"
    (src / "sub").mkdir(parents=True)
    (src / "sub" / "a.txt").write_text("report data")
    arc = encrypt_folder(src, "pw", iterations=FAST)
    assert b"report data" not in arc.read_bytes()
    dest = tmp_path / "restored"
    decrypt_archive(arc, "pw", dest, iterations=FAST)
    assert (dest / "sub" / "a.txt").read_text() == "report data"


def test_zip_slip_is_blocked(tmp_path):
    """Zip entries with path traversal sequences must not escape out_dir."""
    import io
    import zipfile

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("../../evil.txt", b"pwned")
        zf.writestr("safe.txt", b"ok")
    zip_bytes = buf.getvalue()

    blob = encrypt_bytes(zip_bytes, "pw", iterations=FAST)
    archive = tmp_path / "test.orbit.zip"
    archive.write_bytes(blob)

    out_dir = tmp_path / "extracted"
    out_dir.mkdir()
    decrypt_archive(archive, "pw", out_dir, iterations=FAST)

    # The traversal entry must not have escaped
    assert not (tmp_path / "evil.txt").exists()
    # The safe entry should still be extracted
    assert (out_dir / "safe.txt").read_bytes() == b"ok"
