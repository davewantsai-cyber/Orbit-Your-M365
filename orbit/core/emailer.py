"""Email the ORBIT summary on completion (smtplib + email.mime, stdlib only).

Secrets (From address + SMTP password) live in the SecretStore under ``smtp``
(keyring service ``orbit-m365``); host/port/TLS/recipients live in config.toml [email].
Nothing here raises into the caller: failures are logged and reported as ``False``.
"""
from __future__ import annotations

import logging
import re
import smtplib
import ssl
from dataclasses import dataclass, field
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from html import escape
from pathlib import Path

from orbit.core.secrets import SecretStore
from orbit.reporting.context import ReportContext

log = logging.getLogger(__name__)

SECRET_KEY = "smtp"
_ADDR = re.compile(r"^[^@\s,;<>]+@[^@\s,;<>]+\.[^@\s,;<>]+$")
SEV_COLOR = {"Critical": "#b00020", "High": "#d9480f", "Medium": "#b7791f", "Low": "#2b6cb0",
             "Pass": "#2f855a"}


@dataclass
class EmailSettings:
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_tls: bool = True
    from_address: str = ""
    password: str = field(default="", repr=False)
    to_addresses: list[str] = field(default_factory=list)
    cc_addresses: list[str] = field(default_factory=list)

    @property
    def configured(self) -> bool:
        return bool(self.smtp_host and self.from_address and self.to_addresses)


def parse_addresses(text: str) -> list[str]:
    """Split a comma-separated list; raises ValueError on a malformed address."""
    out = [a.strip() for a in text.replace(";", ",").split(",") if a.strip()]
    bad = [a for a in out if not _ADDR.match(a)]
    if bad:
        raise ValueError(f"Invalid email address: {', '.join(bad)}")
    return out


def load_settings(cfg: dict, store: SecretStore | None = None) -> EmailSettings:
    e = cfg["email"]
    secret: dict = {}
    try:
        secret = (store or SecretStore()).load(SECRET_KEY)
    except Exception as exc:  # no passphrase for the file fallback, keyring error...
        log.warning("Could not read SMTP credentials: %s", type(exc).__name__)
    return EmailSettings(e["smtp_host"], int(e["smtp_port"]), bool(e["smtp_tls"]),
                         secret.get("from_address") or e.get("from_address", ""),
                         secret.get("password", ""), list(e["to_addresses"]), list(e["cc_addresses"]))


def build_subject(ctx: ReportContext) -> str:
    return f"ORBIT Assessment — {ctx.report_date} — Score: {round(ctx.summary.posture)}/100"


def build_html(ctx: ReportContext) -> str:
    s = ctx.summary
    rows = "".join(
        f'<tr><td style="padding:4px 12px;color:{SEV_COLOR[sev]};font-weight:bold">{sev}</td>'
        f'<td style="padding:4px 12px;text-align:right">{s.counts[sev]}</td></tr>'
        for sev in ("Critical", "High", "Medium", "Low", "Pass"))
    top = ""
    for f in ctx.top:
        steps = "".join(f"<li>{escape(b)}</li>" for b in ctx.bullets(f))
        top += (f'<h4 style="margin-bottom:2px">{escape(f.title)} '
                f'<span style="color:{SEV_COLOR[f.severity]}">[{f.severity}]</span></h4>'
                f'<div style="color:#666">{escape(f.control_id)} · {escape(f.tool)}</div>'
                f"<p><b>Remediation:</b></p><ul>{steps or '<li>See attached report.</li>'}</ul>")
    return (
        f'<html><body style="font-family:Arial,sans-serif;color:#1a2530">'
        f"<h2>{escape(ctx.title)}</h2>"
        f"<p>Client: <b>{escape(ctx.client)}</b> · Date: {escape(ctx.report_date)}</p>"
        f'<p style="font-size:22px">Posture score: <b>{round(s.posture)}/100</b> '
        f"({s.passed_controls} of {s.total_controls} controls passed)</p>"
        f'<table style="border-collapse:collapse;border:1px solid #ccc">'
        f'<tr><th style="padding:4px 12px;text-align:left">Severity</th>'
        f'<th style="padding:4px 12px">Count</th></tr>{rows}</table>'
        f"<h3>Top findings</h3>{top or '<p>No High or Critical findings.</p>'}"
        f'<p style="color:#888;font-size:12px">{escape(ctx.footer)}</p></body></html>')


def build_message(ctx: ReportContext, pdf_path: Path, settings: EmailSettings) -> MIMEMultipart:
    msg = MIMEMultipart("mixed")
    msg["Subject"] = build_subject(ctx)
    msg["From"] = settings.from_address
    msg["To"] = ", ".join(settings.to_addresses)
    if settings.cc_addresses:
        msg["Cc"] = ", ".join(settings.cc_addresses)
    msg.attach(MIMEText(build_html(ctx), "html", "utf-8"))
    pdf_path = Path(pdf_path)
    part = MIMEApplication(pdf_path.read_bytes(), _subtype="pdf")
    part.add_header("Content-Disposition", "attachment", filename=pdf_path.name)
    msg.attach(part)
    return msg


def _deliver(msg, settings: EmailSettings) -> None:
    recipients = settings.to_addresses + settings.cc_addresses
    if settings.smtp_port == 465 and settings.smtp_tls:
        server = smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=30,
                                  context=ssl.create_default_context())
    else:
        server = smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30)
    with server:
        if settings.smtp_tls and settings.smtp_port != 465:
            server.starttls(context=ssl.create_default_context())
        if settings.password:
            server.login(settings.from_address, settings.password)
        server.sendmail(settings.from_address, recipients, msg.as_string())


def send_results(ctx: ReportContext, pdf_path: Path, config: EmailSettings) -> bool:
    """Build and send the results email. Returns False (and logs) on any failure."""
    try:
        if not config.configured:
            raise ValueError("email is not configured")
        _deliver(build_message(ctx, pdf_path, config), config)
        return True
    except Exception as exc:
        log.error("Email send failed: %s: %s", type(exc).__name__, exc)
        return False


def send_test(config: EmailSettings) -> tuple[bool, str]:
    """Send a short test message; returns (ok, human-readable detail)."""
    try:
        if not config.configured:
            return False, "Fill in host, From address and at least one To address"
        msg = MIMEMultipart()
        msg["Subject"] = "ORBIT test email"
        msg["From"] = config.from_address
        msg["To"] = ", ".join(config.to_addresses)
        if config.cc_addresses:
            msg["Cc"] = ", ".join(config.cc_addresses)
        msg.attach(MIMEText("This is a test message from ORBIT. SMTP settings work.", "plain"))
        _deliver(msg, config)
        return True, "Test email sent"
    except Exception as exc:
        log.error("Test email failed: %s: %s", type(exc).__name__, exc)
        return False, f"{type(exc).__name__}: {exc}"
