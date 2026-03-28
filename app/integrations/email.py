"""
Email integration via Gmail SMTP.
Sends email alerts and reminders.
"""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings


logger = logging.getLogger(__name__)

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465


def _email_is_configured() -> bool:
    return settings.smtp_email != "your@gmail.com" and settings.smtp_password != "your_gmail_app_password"


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

        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(settings.smtp_email, settings.smtp_password)
            server.send_message(msg)

        logger.info("Email sent to %s with subject %s", to, subject)
        return True
    except Exception as exc:
        logger.error("Failed to send email to %s: %s", to, exc)
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
