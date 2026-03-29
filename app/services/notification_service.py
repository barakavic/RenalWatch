"""
Notification service — orchestrates SMS, email alerts, reminders, and chatbot doctor summaries.
"""

import logging

from app.core.config import settings
from app.integrations.africas_talking import send_sms
from app.integrations.email import send_email
from app.nlp.formatter import render_symptom_summary
from app.models.alert import Alert
from app.models.patient import Patient
from app.models.reminder import Reminder
from app.models.symptom_log import SymptomLog


logger = logging.getLogger(__name__)


async def send_alert_notifications(alert: Alert, patient: Patient) -> str:
    channels_used: list[str] = []

    send_to_patient = True
    send_to_doctor = alert.severity in {"high", "critical"}

    if send_to_patient and patient.phone:
        patient_message = _compose_patient_message(alert, patient)
        try:
            patient_response = await send_sms(patient.phone, patient_message)
            if patient_response is not None:
                channels_used.append("sms_patient")
        except Exception as exc:
            logger.warning("Failed to send patient SMS for alert %s: %s", alert.id, exc)

    if send_to_doctor and settings.doctor_phone:
        doctor_sms_message = _compose_doctor_sms_message(alert, patient)
        try:
            doctor_sms_response = await send_sms(settings.doctor_phone, doctor_sms_message)
            if doctor_sms_response is not None:
                channels_used.append("sms_doctor")
        except Exception as exc:
            logger.warning("Failed to send doctor SMS for alert %s: %s", alert.id, exc)

    if send_to_doctor and settings.doctor_email:
        doctor_email_subject = _compose_doctor_email_subject(alert)
        doctor_email_body = _compose_doctor_email_body(alert, patient)
        try:
            email_sent = await send_email(settings.doctor_email, doctor_email_subject, doctor_email_body)
            if email_sent:
                channels_used.append("email_doctor")
        except Exception as exc:
            logger.warning("Failed to send doctor email for alert %s: %s", alert.id, exc)

    if "sms_patient" in channels_used and ("sms_doctor" in channels_used or "email_doctor" in channels_used):
        return "both"
    if any(channel.startswith("sms") for channel in channels_used):
        return "sms"
    if "email_doctor" in channels_used:
        return "email"
    return "none"


async def send_reminder_notification(reminder: Reminder, patient: Patient) -> str:
    channels_used: list[str] = []

    try:
        sms_response = await send_sms(patient.phone, reminder.message)
        if sms_response is not None:
            channels_used.append("sms")
    except Exception as exc:
        logger.warning("Failed to send reminder SMS for patient %s: %s", patient.id, exc)

    if reminder.reminder_type == "appointment" and patient.email:
        try:
            email_sent = await send_email(
                to=patient.email,
                subject="RenalWatch reminder",
                body=reminder.message,
            )
            if email_sent:
                channels_used.append("email")
        except Exception as exc:
            logger.warning("Failed to send reminder email for patient %s: %s", patient.id, exc)

    if "sms" in channels_used and "email" in channels_used:
        return "sms,email"
    if "email" in channels_used:
        return "email"
    if "sms" in channels_used:
        return "sms"
    return "none"


async def notify_doctor_symptoms(patient: Patient, log: SymptomLog) -> str:
    summary = render_symptom_summary(
        patient_name=patient.name,
        fatigue=log.fatigue,
        pain_level=log.pain_level,
        swelling=log.swelling,
        nausea=log.nausea,
        notes=log.notes,
    )

    channels_used: list[str] = []

    if settings.doctor_phone:
        sms_message = (
            f"Symptom Summary: {patient.name} check-in complete. "
            f"Fatigue/Pain/Swelling/Nausea: "
            f"{log.fatigue}/{log.pain_level}/{log.swelling}/{log.nausea}."
        )
        try:
            sms_response = await send_sms(settings.doctor_phone, sms_message)
            if sms_response is not None:
                channels_used.append("sms")
        except Exception as exc:
            logger.warning("Failed to send doctor symptom SMS for patient %s: %s", patient.id, exc)

    if settings.doctor_email:
        try:
            email_sent = await send_email(
                to=settings.doctor_email,
                subject=f"Patient Check-in - {patient.name}",
                body=summary,
            )
            if email_sent:
                channels_used.append("email")
        except Exception as exc:
            logger.warning("Failed to send doctor symptom email for patient %s: %s", patient.id, exc)

    if "sms" in channels_used and "email" in channels_used:
        return "sms,email"
    if "email" in channels_used:
        return "email"
    if "sms" in channels_used:
        return "sms"
    return "none"


def _compose_patient_message(alert: Alert, patient: Patient) -> str:
    if alert.alert_type == "crisis":
        return (
            f"{patient.name}, critical BP alert: {alert.message} "
            "Please contact your doctor or seek immediate help."
        )
    if alert.alert_type == "stage2":
        return f"{patient.name}, your BP is elevated: {alert.message}"
    if alert.alert_type == "missed_reading":
        return f"{patient.name}, you've missed your BP reading. Please take one when you can."
    return f"{patient.name}, alert: {alert.message}"


def _compose_doctor_sms_message(alert: Alert, patient: Patient) -> str:
    return (
        f"[{alert.severity.upper()}] {alert.alert_type.upper()} for {patient.name} "
        f"(CKD stage {patient.ckd_stage}): {alert.message}"
    )


def _compose_doctor_email_subject(alert: Alert) -> str:
    return f"RenalWatch [{alert.severity.upper()}] {alert.alert_type.replace('_', ' ').title()}"


def _compose_doctor_email_body(alert: Alert, patient: Patient) -> str:
    return f"""
RENAL WATCH — PATIENT ALERT

Severity:       {alert.severity.upper()}
Alert Type:     {alert.alert_type.replace('_', ' ').title()}
Patient:        {patient.name} (ID: {patient.id})
Patient Phone:  {patient.phone}
Patient Email:  {patient.email or 'N/A'}
CKD Stage:      {patient.ckd_stage}
Age:            {patient.age}

Message:
{alert.message}

Clinical Explanation:
{alert.explanation}

Triggered At:   {alert.triggered_at.isoformat() if alert.triggered_at else 'N/A'}
""".strip()
