"""
Africa's Talking SMS integration wrapper.
"""

import logging

import africastalking

from app.core.config import settings


logger = logging.getLogger(__name__)
_initialized = False


def _sms_is_configured() -> bool:
    return settings.at_api_key != "your_africas_talking_live_api_key"


def _ensure_initialized() -> None:
    global _initialized
    if _initialized or not _sms_is_configured():
        return

    africastalking.initialize(username=settings.at_username, api_key=settings.at_api_key)
    _initialized = True


async def send_sms(phone: str, message: str) -> dict | None:
    if not phone or not _sms_is_configured():
        logger.info("Skipping SMS send because Africa's Talking credentials are placeholders.")
        return None

    try:
        _ensure_initialized()
        sms = africastalking.SMS
        response = sms.send(message, [phone])
        logger.info("SMS sent to %s", phone)
        return response
    except Exception as exc:
        logger.error("Failed to send SMS to %s: %s", phone, exc)
        raise


async def send_bulk_sms(recipients: list[str], message: str) -> dict | None:
    valid_recipients = [recipient for recipient in recipients if recipient]
    if not valid_recipients or not _sms_is_configured():
        logger.info("Skipping bulk SMS send because recipients or credentials are missing.")
        return None

    try:
        _ensure_initialized()
        sms = africastalking.SMS
        response = sms.send(message, valid_recipients)
        logger.info("Bulk SMS sent to %s recipients", len(valid_recipients))
        return response
    except Exception as exc:
        logger.error("Failed to send bulk SMS: %s", exc)
        raise
