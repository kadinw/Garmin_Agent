"""Send the Garmin export through Gmail SMTP."""

from __future__ import annotations

import logging
import smtplib
import ssl
from email.message import EmailMessage
from pathlib import Path

from garmin_agent.config import Settings

LOGGER = logging.getLogger(__name__)


def send_report(
    settings: Settings,
    subject: str,
    body: str,
    attachments: list[Path],
) -> None:
    message = EmailMessage()
    message["From"] = settings.email
    message["To"] = settings.recipient
    message["Subject"] = subject
    message.set_content(body)

    for path in attachments:
        data = path.read_bytes()
        subtype = "json" if path.suffix == ".json" else "csv"
        message.add_attachment(
            data,
            maintype="application" if subtype == "json" else "text",
            subtype=subtype,
            filename=path.name,
        )

    context = ssl.create_default_context()
    LOGGER.info("Sending Garmin report to %s via %s", settings.recipient, settings.smtp_host)
    try:
        _smtp_send(settings, message, context)
    except smtplib.SMTPAuthenticationError as exc:
        code, response = exc.smtp_code, exc.smtp_error
        detail = response.decode("utf-8", errors="replace") if isinstance(response, bytes) else str(response)
        raise RuntimeError(
            f"Gmail rejected the SMTP login (code {code}: {detail}). "
            "Confirm line 3 is an App Password created while signed into "
            f"{settings.email} at https://myaccount.google.com/apppasswords."
        ) from exc
    LOGGER.info("Email sent.")


def _smtp_send(settings: Settings, message: EmailMessage, context: ssl.SSLContext) -> None:
    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=60) as smtp:
            smtp.ehlo()
            smtp.starttls(context=context)
            smtp.ehlo()
            smtp.login(settings.email, settings.smtp_password)
            smtp.send_message(message)
            return
    except smtplib.SMTPAuthenticationError:
        raise
    except OSError:
        LOGGER.info("Port %s failed; retrying Gmail SMTP over SSL on 465.", settings.smtp_port)

    with smtplib.SMTP_SSL(settings.smtp_host, 465, timeout=60, context=context) as smtp:
        smtp.login(settings.email, settings.smtp_password)
        smtp.send_message(message)
