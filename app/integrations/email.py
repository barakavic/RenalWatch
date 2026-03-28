"""
Email integration via Gmail SMTP.
Sends email alerts to doctors and patients.
"""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.core.config import settings

logger = logging.getLogger(__name__)

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465


async def send_email(to: str, subject: str, body: str, body_html: str = None) -> bool:
    """
    Send an email via Gmail SMTP.

    Args:
        to: Recipient email address
        subject: Email subject line
        body: Plain text email body
        body_html: Optional HTML version of the email body

    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.smtp_email
        msg["To"] = to

        # Attach plain text part
        msg.attach(MIMEText(body, "plain"))

        # Attach HTML part if provided
        if body_html:
            msg.attach(MIMEText(body_html, "html"))

        # Send via Gmail SMTP
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(settings.smtp_email, settings.smtp_password)
            server.send_message(msg)

        logger.info(f"Email sent to {to} with subject: {subject}")
        return True

    except Exception as e:
        logger.error(f"Failed to send email to {to}: {str(e)}")
        return False


async def send_bulk_email(recipients: list[str], subject: str, body: str, body_html: str = None) -> dict:
    """
    Send the same email to multiple recipients.

    Args:
        recipients: List of email addresses
        subject: Email subject line
        body: Plain text email body
        body_html: Optional HTML version

    Returns:
        dict: {"sent": count, "failed": count}
    """
    results = {"sent": 0, "failed": 0}

    for recipient in recipients:
        success = await send_email(recipient, subject, body, body_html)
        if success:
            results["sent"] += 1
        else:
            results["failed"] += 1

    logger.info(f"Bulk email results: {results['sent']} sent, {results['failed']} failed")
    return results
