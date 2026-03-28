"""
Notification service — orchestrates SMS and email alerts.
Routes alerts to patients and doctors via multiple channels.
"""

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert
from app.models.patient import Patient
from app.core.config import settings
from app.integrations import africas_talking, email

logger = logging.getLogger(__name__)


async def send_alert_notification(
    session: AsyncSession,
    alert: Alert,
    send_to_patient: bool = True,
    send_to_doctor: bool = False,
) -> None:
    """
    Send alert notification to patient and/or doctor via SMS and/or email.

    Handles:
    - Fetching patient contact info
    - Composing contextual messages
    - Calling SMS and email integrations
    - Updating alert record with sent_via status
    - Logging outcomes

    Args:
        session: AsyncSession for database operations
        alert: Alert object from database (must have patient_id, message, severity, etc.)
        send_to_patient: Whether to send SMS to patient (default: True)
        send_to_doctor: Whether to notify doctor via SMS + Email (default: False for low severity)
    """
    try:
        # Fetch patient details
        stmt = select(Patient).where(Patient.id == alert.patient_id)
        result = await session.execute(stmt)
        patient = result.scalar_one()

        if not patient:
            logger.error(f"Patient {alert.patient_id} not found for alert {alert.id}")
            return

        channels_used = []
        failures = []

        # Send SMS to patient if requested
        if send_to_patient and patient.phone:
            try:
                patient_message = _compose_patient_message(alert, patient)
                await africas_talking.send_sms(patient.phone, patient_message)
                channels_used.append("sms_patient")
                logger.info(f"Alert {alert.id}: SMS sent to patient {patient.id}")
            except Exception as e:
                logger.error(f"Alert {alert.id}: Failed to send SMS to patient: {str(e)}")
                failures.append(f"sms_patient: {str(e)}")

        # Send SMS to doctor if high severity
        if send_to_doctor and settings.doctor_phone:
            try:
                doctor_sms_message = _compose_doctor_sms_message(alert, patient)
                await africas_talking.send_sms(settings.doctor_phone, doctor_sms_message)
                channels_used.append("sms_doctor")
                logger.info(f"Alert {alert.id}: SMS sent to doctor")
            except Exception as e:
                logger.error(f"Alert {alert.id}: Failed to send SMS to doctor: {str(e)}")
                failures.append(f"sms_doctor: {str(e)}")

        # Send email to doctor if high severity
        if send_to_doctor and settings.doctor_email:
            try:
                doctor_email_subject = _compose_doctor_email_subject(alert)
                doctor_email_body = _compose_doctor_email_body(alert, patient)
                success = await email.send_email(
                    settings.doctor_email,
                    doctor_email_subject,
                    doctor_email_body,
                )
                if success:
                    channels_used.append("email_doctor")
                    logger.info(f"Alert {alert.id}: Email sent to doctor")
                else:
                    failures.append("email_doctor: SMTP error")
            except Exception as e:
                logger.error(f"Alert {alert.id}: Failed to send email to doctor: {str(e)}")
                failures.append(f"email_doctor: {str(e)}")

        # Update alert record with sent_via
        if channels_used:
            alert.sent_via = ",".join(channels_used)
            session.add(alert)
            await session.commit()
            logger.info(f"Alert {alert.id} sent via: {alert.sent_via}")
        else:
            logger.warning(f"Alert {alert.id}: No channels successfully sent. Failures: {failures}")

    except Exception as e:
        logger.error(f"Unexpected error in send_alert_notification: {str(e)}")


async def notify_patient_critical_alert(
    session: AsyncSession,
    patient_id: int,
    alert_type: str,
    message: str,
    severity: str,
    explanation: str,
) -> Alert:
    """
    Create and send a critical alert to patient.

    High-level convenience function for route handlers.

    Args:
        session: AsyncSession
        patient_id: Patient ID
        alert_type: Type of alert ("spike", "stage2", "crisis", "missed_reading")
        message: Alert message text
        severity: Severity level ("low", "medium", "high", "critical")
        explanation: XAI explanation string

    Returns:
        Alert: Created alert record
    """
    alert = Alert(
        patient_id=patient_id,
        alert_type=alert_type,
        message=message,
        severity=severity,
        explanation=explanation,
        sent_via="pending",
    )
    session.add(alert)
    await session.flush()

    # Decide routing based on severity
    send_to_patient = severity in ["high", "critical"]
    send_to_doctor = severity in ["high", "critical"]

    await send_alert_notification(session, alert, send_to_patient, send_to_doctor)
    await session.refresh(alert)

    return alert


# --- Message composition helpers ---


def _compose_patient_message(alert: Alert, patient: Patient) -> str:
    """
    Compose SMS message for patient.
    Keep under 160 chars where possible for single SMS.
    """
    if alert.alert_type == "crisis":
        return f"🚨 {patient.name}, HIGH ALERT: {alert.message}. Contact your doctor immediately or call 911."

    elif alert.alert_type == "spike":
        return f"⚠️ {patient.name}, your BP spike was detected. {alert.message} Please monitor closely."

    elif alert.alert_type == "stage2":
        return f"📊 {patient.name}, your BP entered Stage 2 Hypertension range. {alert.message}"

    elif alert.alert_type == "missed_reading":
        return f"📋 {patient.name}, you've missed your BP reading today. Please take one when you can."

    else:
        return f"📱 {patient.name}, Alert: {alert.message}"


def _compose_doctor_sms_message(alert: Alert, patient: Patient) -> str:
    """
    Compose SMS message for doctor.
    More clinical detail in shorter form.
    """
    severity_icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(
        alert.severity, "⚪"
    )
    return (
        f"{severity_icon} [{alert.alert_type.upper()}] Patient {patient.name} ({patient.id}): "
        f"{alert.message}. CKD Stage: {patient.ckd_stage}. "
        f"Check dashboard for details."
    )


def _compose_doctor_email_subject(alert: Alert) -> str:
    """Compose email subject for doctor."""
    severity_prefix = {
        "critical": "[CRITICAL]",
        "high": "[HIGH]",
        "medium": "[MEDIUM]",
        "low": "[LOW]",
    }.get(alert.severity, "[ALERT]")

    return f"RenalWatch {severity_prefix} {alert.alert_type.replace('_', ' ').title()}"


def _compose_doctor_email_body(alert: Alert, patient: Patient) -> str:
    """Compose complete email body for doctor with clinical details."""
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

---
Action Required: Review the patient dashboard for trends, anomalies, and recent symptom logs.
http://localhost:3000/dashboard/{patient.id}

RenalWatch System
Not a diagnostic tool — a monitoring and alerting system.
""".strip()
