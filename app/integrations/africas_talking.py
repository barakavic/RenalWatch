"""
Africa's Talking SMS / WhatsApp integration wrapper.
"""

import logging

import africastalking

from app.core.config import settings


logger = logging.getLogger(__name__)
_initialized = False


def _at_is_configured() -> bool:
    return (
        settings.at_api_key != "your_africas_talking_live_api_key"
        and bool(settings.at_username)
    )


def _ensure_initialized() -> None:
    global _initialized
    if _initialized or not _at_is_configured():
        return

    africastalking.initialize(username=settings.at_username, api_key=settings.at_api_key)
    _initialized = True


async def send_sms(phone: str, message: str) -> dict | None:
    if not phone or not _at_is_configured():
        logger.info("Skipping SMS send because Africa's Talking credentials are placeholders.")
        return None

    try:
        _ensure_initialized()
        sms = africastalking.SMS
        kwargs = {"message": message, "recipients": [phone]}
        if settings.at_sender_id:
            kwargs["sender_id"] = settings.at_sender_id
        response = sms.send(**kwargs)
        logger.info("SMS sent to %s", phone)
        return response
    except Exception as exc:
        logger.error("Failed to send SMS to %s: %s", phone, exc)
        raise


async def send_bulk_sms(recipients: list[str], message: str) -> dict | None:
    valid_recipients = [recipient for recipient in recipients if recipient]
    if not valid_recipients or not _at_is_configured():
        logger.info("Skipping bulk SMS send because recipients or credentials are missing.")
        return None

    try:
        _ensure_initialized()
        sms = africastalking.SMS
        kwargs = {"message": message, "recipients": valid_recipients}
        if settings.at_sender_id:
            kwargs["sender_id"] = settings.at_sender_id
        response = sms.send(**kwargs)
        logger.info("Bulk SMS sent to %s recipients", len(valid_recipients))
        return response
    except Exception as exc:
        logger.error("Failed to send bulk SMS: %s", exc)
        raise


def send_whatsapp_message(phone: str, message: str) -> bool:
    if not phone:
        logger.info("Skipping WhatsApp send because recipient is missing.")
        return False

    # For the demo, we keep the webhook/chatbot live and optionally use SMS as the transport fallback.
    if settings.whatsapp_demo_fallback_to_sms and _at_is_configured():
        try:
            _ensure_initialized()
            sms = africastalking.SMS
            kwargs = {"message": f"[WhatsApp Demo] {message}", "recipients": [phone]}
            if settings.at_sender_id:
                kwargs["sender_id"] = settings.at_sender_id
            sms.send(**kwargs)
            logger.info("WhatsApp demo fallback sent to %s via SMS transport", phone)
            return True
        except Exception as exc:
            logger.warning("WhatsApp demo fallback failed for %s: %s", phone, exc)

    logger.info("[AT WHATSAPP MOCK] To %s: %s", phone, message)
    return False
