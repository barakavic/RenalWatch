"""
Africa's Talking SMS integration wrapper.
Sends SMS alerts to patients and doctors.
"""

import logging
from typing import Optional

import africastalking

from app.core.config import settings

logger = logging.getLogger(__name__)

# Initialize Africa's Talking
africastalking.initialize(username=settings.at_username, api_key=settings.at_api_key)
sms = africastalking.SMS


async def send_sms(phone: str, message: str) -> dict:
    """
    Send an SMS message to a phone number via Africa's Talking.

    Args:
        phone: Phone number in E.164 format (e.g., +254700000000)
        message: SMS message body (max 160 chars for standard SMS)

    Returns:
        dict: Response from Africa's Talking API
            {
                "SMSMessageData": {
                    "Message": "Sent to 1/1 recipients",
                    "Recipients": [
                        {
                            "number": "+254700000000",
                            "status": "Success",
                            "messageId": "ATXid_..."
                        }
                    ]
                }
            }

    Raises:
        Exception: If SMS sending fails
    """
    try:
        response = sms.send(message, [phone])
        logger.info(f"SMS sent to {phone}: {response}")
        return response
    except Exception as e:
        logger.error(f"Failed to send SMS to {phone}: {str(e)}")
        raise


async def send_bulk_sms(recipients: list[str], message: str) -> dict:
    """
    Send the same SMS message to multiple recipients.

    Args:
        recipients: List of phone numbers in E.164 format
        message: SMS message body

    Returns:
        dict: Response from Africa's Talking API
    """
    try:
        response = sms.send(message, recipients)
        logger.info(f"Bulk SMS sent to {len(recipients)} recipients: {response}")
        return response
    except Exception as e:
        logger.error(f"Failed to send bulk SMS: {str(e)}")
        raise
