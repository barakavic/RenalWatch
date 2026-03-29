import logging

from twilio.rest import Client

from app.core.config import settings


logger = logging.getLogger(__name__)


def _twilio_is_configured() -> bool:
    return bool(settings.twilio_account_sid and settings.twilio_auth_token and settings.twilio_whatsapp_from)


def send_whatsapp_message(phone: str, message: str) -> bool:
    if not phone or not _twilio_is_configured():
        logger.info("Skipping Twilio WhatsApp send because credentials or recipient are missing.")
        return False

    to_number = phone if phone.startswith("whatsapp:") else f"whatsapp:{phone}"

    try:
        client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
        result = client.messages.create(
            from_=settings.twilio_whatsapp_from,
            to=to_number,
            body=message,
        )
        logger.info("Twilio WhatsApp message sent to %s with sid %s", to_number, result.sid)
        return True
    except Exception as exc:
        logger.error("Failed to send Twilio WhatsApp message to %s: %s", to_number, exc)
        return False
