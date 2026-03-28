import africastalking

from app.core.config import settings


_initialized = False


def _ensure_initialized() -> None:
    global _initialized
    if _initialized:
        return

    africastalking.initialize(username=settings.at_username, api_key=settings.at_api_key)
    _initialized = True


def send_sms(phone: str, message: str) -> dict:
    _ensure_initialized()
    sms = africastalking.SMS
    return sms.send(message, [phone])
