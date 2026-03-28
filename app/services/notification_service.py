import logging
from app.models.patient import Patient
from app.models.symptom_log import SymptomLog
from app.integrations.africas_talking import send_sms
from app.core.config import settings

logger = logging.getLogger(__name__)

async def notify_doctor_symptoms(patient: Patient, log: SymptomLog):
    """
    Called when a patient completes the WhatsApp symptom check-in flow.
    Sends a summary SMS and Email to the doctor.
    """
    summary = (
        f"RenalWatch Update for {patient.name} (Phone: {patient.phone}):\n"
        f"Fatigue: {log.fatigue}/10\n"
        f"Pain: {log.pain_level}/10\n"
        f"Swelling: {log.swelling}/10\n"
        f"Nausea: {log.nausea}/10\n"
        f"Notes: {log.notes}"
    )

    logger.info(f"\n--- NOTIFYING DOCTOR: {settings.DOCTOR_PHONE} ---\n{summary}\n-------------------------")
    
    # Send SMS via AT Mock
    send_sms(settings.DOCTOR_PHONE, f"Symptom Summary: {patient.name} check-in complete. Fatigue/Pain/Swelling: {log.fatigue}/{log.pain_level}/{log.swelling}. Check dash for details.")
    
    # Mock sending Email
    logger.info(f"[EMAIL MOCK] To: {settings.DOCTOR_EMAIL} | Subject: Patient Check-in - {patient.name}\nBody: {summary}")
