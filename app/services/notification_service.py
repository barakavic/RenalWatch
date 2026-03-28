from app.core.config import settings
from app.integrations.africas_talking import send_sms
from app.models.alert import Alert
from app.models.patient import Patient


async def send_alert_notifications(alert: Alert, patient: Patient) -> str:
    recipients = [patient.phone]

    if alert.severity == "critical" and settings.doctor_phone not in recipients:
        recipients.append(settings.doctor_phone)

    for phone in recipients:
        send_sms(phone, alert.message)

    return "sms"
