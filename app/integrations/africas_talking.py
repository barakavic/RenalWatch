import logging
from app.core.config import settings
import africastalking

logger = logging.getLogger(__name__)

# Initialize Africa's Talking (even if dummy/sandbox credentials are provided)
try:
    africastalking.initialize(username=settings.AT_USERNAME, api_key=settings.AT_API_KEY)
    sms = africastalking.SMS
except Exception as e:
    logger.warning(f"Failed to initialize Africa's Talking SDK: {e}")
    sms = None

def send_sms(phone: str, message: str):
    """
    Simulates sending an SMS or sends it if credentials are real/sandbox.
    """
    logger.info(f"[AT SMS MOCK] To {phone}: {message}")
    if sms and settings.AT_USERNAME != "sandbox":
        try:
            return sms.send(message, [phone])
        except Exception as e:
            logger.error(f"Error sending SMS via AT: {e}")
    return {"status": "mocked", "message": "Check logs"}

def send_whatsapp_message(phone: str, message: str):
    """
    Simulates sending a WhatsApp message or uses the SMS SDK since AT WhatsApp 
    follows a similar pattern for sending responses.
    For this prototype (with no funds/money), we'll mock the print out.
    """
    logger.info(f"\n[AT WHATSAPP MOCK] To {phone}: {message}\n")
    # Real implementation would use AT's WhatsApp endpoint or SMS wrapper for WhatsApp channel
    pass
