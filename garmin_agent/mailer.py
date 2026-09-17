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
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=60) as smtp:
            smtp.ehlo()
            smtp.starttls(context=context)
            smtp.ehlo()
            smtp.login(settings.email, settings.smtp_password)
            smtp.send_message(message)
    except smtplib.SMTPAuthenticationError as exc:
        raise RuntimeError(
            "Gmail rejected the SMTP login. If 2-Step Verification is on, put a "
            "Gmail App Password on line 3 of secrets/.env.txt "
            "(https://myaccount.google.com/apppasswords)."
        ) from exc
    LOGGER.info("Email sent.")
