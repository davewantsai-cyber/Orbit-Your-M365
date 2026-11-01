from email import message_from_string
from pathlib import Path
from unittest.mock import patch

import pytest

from orbit.core import emailer
from orbit.reporting import parser
from orbit.reporting.context import ReportContext
from orbit.reporting.pdf_report import generate_pdf

FIX = Path(__file__).parent / "fixtures"


@pytest.fixture()
def ctx():
    f = parser.parse_files({"scubagear": FIX / "scubagear_sample.json",
                            "maester": FIX / "maester_sample.json"})
    return ReportContext(f, ["ScubaGear", "Maester"], dry_run=True, client="Acme Ltd")


@pytest.fixture()
def settings():
    return emailer.EmailSettings("smtp.example.com", 587, True, "orbit@example.com", "pw",
                                 ["to@example.com"], ["cc@example.com"])


def _mock_smtp(cls):
    server = cls.return_value
    server.__enter__.return_value = server  # like real smtplib: __enter__ returns self
    return server


def test_send_results_builds_correct_message(ctx, settings, tmp_path):
    pdf = generate_pdf(ctx, tmp_path, use_unicode=False)
    with patch("orbit.core.emailer.smtplib.SMTP") as smtp:
        server = _mock_smtp(smtp)
        assert emailer.send_results(ctx, pdf, settings) is True
    smtp.assert_called_once_with("smtp.example.com", 587, timeout=30)
    server.starttls.assert_called_once()
    server.login.assert_called_once_with("orbit@example.com", "pw")
    sender, recipients, raw = server.sendmail.call_args.args
    assert sender == "orbit@example.com" and recipients == ["to@example.com", "cc@example.com"]
    msg = message_from_string(raw)
    subject = str(message_from_string(raw)["Subject"])
    assert emailer.build_subject(ctx) == f"ORBIT Assessment — {ctx.report_date} — Score: 50/100"
    assert subject  # non-ASCII subject is RFC 2047-encoded on the wire
    assert msg["To"] == "to@example.com" and msg["Cc"] == "cc@example.com"
    parts = list(msg.walk())
    assert any(p.get_filename() == pdf.name for p in parts)
    html = next(p for p in parts if p.get_content_type() == "text/html")
    body = html.get_payload(decode=True).decode()
    assert "50/100" in body and "Critical" in body and "Acme Ltd" in body
    assert body.count("Remediation:") == 3


def test_subject_header_decodes(ctx, settings, tmp_path):
    from email.header import decode_header, make_header
    msg = emailer.build_message(ctx, generate_pdf(ctx, tmp_path, use_unicode=False), settings)
    assert str(make_header(decode_header(msg["Subject"]))) == emailer.build_subject(ctx)


def test_failure_does_not_raise(ctx, settings, tmp_path):
    pdf = generate_pdf(ctx, tmp_path, use_unicode=False)
    with patch("orbit.core.emailer.smtplib.SMTP", side_effect=OSError("down")):
        assert emailer.send_results(ctx, pdf, settings) is False
    assert emailer.send_results(ctx, pdf, emailer.EmailSettings()) is False


def test_parse_addresses():
    assert emailer.parse_addresses("a@x.com, b@y.org;") == ["a@x.com", "b@y.org"]
    assert emailer.parse_addresses("") == []
    with pytest.raises(ValueError):
        emailer.parse_addresses("a@x.com, not-an-address")
    with pytest.raises(ValueError):
        emailer.parse_addresses("a@x.com\nBcc: evil@x.com")


def test_send_test_and_ssl_port(settings):
    settings.smtp_port = 465
    with patch("orbit.core.emailer.smtplib.SMTP_SSL") as ssl_smtp:
        _mock_smtp(ssl_smtp)
        ok, _ = emailer.send_test(settings)
    assert ok and ssl_smtp.called
    assert emailer.send_test(emailer.EmailSettings())[0] is False
