"""Secret storage: OS keychain (keyring) primary, Fernet/PBKDF2 encrypted file fallback.

Secrets are never written in plaintext, never logged, and are masked with '***'.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from orbit.security.encryption import decrypt_bytes, encrypt_bytes

SERVICE = "orbit-m365"
MASK = "***"
DEFAULT_FALLBACK = Path.home() / ".orbit" / "secrets.enc"


@dataclass(frozen=True)
class Field:
    name: str
    label: str
    secret: bool = False
    kind: str = "text"  # text | bool | choice
    choices: tuple[str, ...] = ()


TOOL_FIELDS: dict[str, list[Field]] = {
    "scubagear": [
        Field("tenant_id", "Tenant ID"),
        Field("client_id", "App Client ID"),
        Field("auth_method", "Auth method", kind="choice", choices=("certificate", "client_secret")),
        Field("cert_thumbprint", "Certificate thumbprint", secret=True),
        Field("client_secret", "Client secret", secret=True),
        Field("admin_upn", "Admin UPN (optional)"),
    ],
    "maester": [
        Field("tenant_id", "Tenant ID"),
        Field("client_id", "App Client ID"),
        Field("auth_method", "Auth method", kind="choice", choices=("certificate", "client_secret")),
        Field("cert_thumbprint", "Certificate thumbprint", secret=True),
        Field("client_secret", "Client secret", secret=True),
        Field("admin_upn", "Admin UPN (optional)"),
    ],
    "monkey365": [
        Field("tenant_id", "Tenant ID"),
        Field("client_id", "App ID"),
        Field("client_secret", "Client secret", secret=True),
        Field("subscription_id", "Subscription ID"),
    ],
    "roadtools": [
        Field("client_id", "Client ID"),
        Field("device_code", "Use device-code flow", kind="bool"),
    ],
    "hawk": [Field("admin_upn", "Global Admin UPN")],
}


def secret_field_names(tool: str) -> set[str]:
    return {f.name for f in TOOL_FIELDS.get(tool, []) if f.secret}


def mask(value: str | None) -> str:
    return MASK if value else ""


def redact(text: str, secrets: list[str]) -> str:
    """Replace every known secret value in text with '***' (for log output)."""
    for s in sorted((s for s in secrets if s), key=len, reverse=True):
        text = text.replace(s, MASK)
    return text


class SecretStore:
    """Stores per-tool field dicts. Keyring when usable, else encrypted file (needs passphrase)."""

    def __init__(self, passphrase: str | None = None, fallback_path: Path | None = None,
                 use_keyring: bool | None = None, iterations: int | None = None):
        self._passphrase = passphrase
        self._path = fallback_path or DEFAULT_FALLBACK
        self._iter = iterations
        self.use_keyring = self._keyring_usable() if use_keyring is None else use_keyring

    @staticmethod
    def _keyring_usable() -> bool:
        try:
            import keyring
            from keyring.backends import fail

            return not isinstance(keyring.get_keyring(), fail.Keyring)
        except Exception:
            return False

    @property
    def backend(self) -> str:
        return "keyring" if self.use_keyring else "encrypted-file"

    # -- file fallback -------------------------------------------------
    def _kw(self) -> dict:
        return {"iterations": self._iter} if self._iter else {}

    def _load_file(self) -> dict:
        if not self._path.exists():
            return {}
        if not self._passphrase:
            raise PermissionError("Passphrase required for encrypted secret store")
        return json.loads(decrypt_bytes(self._path.read_bytes(), self._passphrase, **self._kw()))

    def _save_file(self, data: dict) -> None:
        if not self._passphrase:
            raise PermissionError("Passphrase required for encrypted secret store")
        self._path.parent.mkdir(parents=True, exist_ok=True)
        blob = encrypt_bytes(json.dumps(data).encode(), self._passphrase, **self._kw())
        self._path.write_bytes(blob)
        try:
            self._path.chmod(0o600)
        except OSError:
            pass

    # -- public API ----------------------------------------------------
    def save(self, tool: str, values: dict) -> None:
        if self.use_keyring:
            import keyring

            keyring.set_password(SERVICE, tool, json.dumps(values))
        else:
            data = self._load_file()
            data[tool] = values
            self._save_file(data)

    def load(self, tool: str) -> dict:
        if self.use_keyring:
            import keyring

            raw = keyring.get_password(SERVICE, tool)
            return json.loads(raw) if raw else {}
        return self._load_file().get(tool, {})

    def delete(self, tool: str) -> None:
        if self.use_keyring:
            import keyring

            try:
                keyring.delete_password(SERVICE, tool)
            except keyring.errors.PasswordDeleteError:
                pass
        else:
            data = self._load_file()
            data.pop(tool, None)
            self._save_file(data)

    def masked(self, tool: str) -> dict:
        secret = secret_field_names(tool)
        return {k: (mask(v) if k in secret else v) for k, v in self.load(tool).items()}

    def secret_values(self, tool: str) -> list[str]:
        names = secret_field_names(tool)
        return [str(v) for k, v in self.load(tool).items() if k in names and v]
