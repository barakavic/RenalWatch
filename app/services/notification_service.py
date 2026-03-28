from app.core.config import settings
from app.integrations.africas_talking import send_sms
from app.integrations.email import send_email
from app.models.alert import Alert
from app.models.patient import Patient
from app.models.reminder import Reminder


async def send_alert_notifications(alert: Alert, patient: Patient) -> str:
    recipients = [patient.phone]

    if alert.severity == "critical" and settings.doctor_phone not in recipients:
        recipients.append(settings.doctor_phone)

    for phone in recipients:
        send_sms(phone, alert.message)

    return "sms"


async def send_reminder_notification(reminder: Reminder, patient: Patient) -> str:
    send_sms(patient.phone, reminder.message)

    if reminder.reminder_type == "appointment" and patient.email:
        send_email(
            to=patient.email,
            subject="RenalWatch reminder",
            body=reminder.message,
        )
        return "sms,email"

    return "sms"
