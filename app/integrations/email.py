"""
Email integration via Gmail SMTP.
Sends email alerts and reminders.
"""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import httpx

from app.core.config import settings


logger = logging.getLogger(__name__)


def _email_is_configured() -> bool:
    return settings.smtp_email != "your@gmail.com" and settings.smtp_password != "your_gmail_app_password"


async def _send_via_relay(to: str, subject: str, body: str, body_html: str = None) -> bool:
    if not settings.email_relay_url:
        return False

    payload = {
        "to": to,
        "subject": subject,
        "body": body,
        "body_html": body_html,
        "smtp_email": settings.smtp_email,
        "smtp_password": settings.smtp_password,
        "smtp_server": settings.smtp_server,
        "smtp_port": settings.smtp_port,
        "smtp_use_ssl": settings.smtp_use_ssl,
        "smtp_timeout": settings.smtp_timeout,
    }
    headers = {"X-Relay-Token": settings.email_relay_token}

    try:
        async with httpx.AsyncClient(timeout=settings.smtp_timeout + 5) as client:
            response = await client.post(settings.email_relay_url, json=payload, headers=headers)
        response.raise_for_status()
        logger.info("Email sent via host relay to %s", to)
        return True
    except Exception as exc:
        logger.error("Failed to send email via host relay to %s: %s", to, exc)
        return False


async def send_email(to: str, subject: str, body: str, body_html: str = None) -> bool:
    if not to or not _email_is_configured():
        logger.info("Skipping email send because SMTP credentials are placeholders or recipient is missing.")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.smtp_email
        msg["To"] = to

        msg.attach(MIMEText(body, "plain"))
        if body_html:
            msg.attach(MIMEText(body_html, "html"))

        if settings.smtp_use_ssl:
            server = smtplib.SMTP_SSL(
                settings.smtp_server,
                settings.smtp_port,
                timeout=settings.smtp_timeout,
            )
        else:
            server = smtplib.SMTP(
                settings.smtp_server,
                settings.smtp_port,
                timeout=settings.smtp_timeout,
            )
            server.starttls()

        with server:
            server.login(settings.smtp_email, settings.smtp_password)
            server.send_message(msg)

        logger.info("Email sent to %s with subject %s", to, subject)
        return True
    except Exception as exc:
        logger.error("Failed to send email to %s: %s", to, exc)
        if any(token in str(exc) for token in ("Network is unreachable", "timed out", "Temporary failure")):
            return await _send_via_relay(to, subject, body, body_html)
        return False


async def send_bulk_email(recipients: list[str], subject: str, body: str, body_html: str = None) -> dict:
    results = {"sent": 0, "failed": 0}

    for recipient in recipients:
        success = await send_email(recipient, subject, body, body_html)
        if success:
            results["sent"] += 1
        else:
            results["failed"] += 1

    logger.info("Bulk email results: %s sent, %s failed", results["sent"], results["failed"])
    return results
