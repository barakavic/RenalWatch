from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert
from app.models.bp_reading import BPReading
from app.models.patient import Patient
from app.services.notification_service import send_alert_notifications


async def evaluate_reading_for_alerts(reading: BPReading, patient: Patient, db: AsyncSession) -> Alert | None:
    if reading.systolic <= 180:
        return None

    alert = Alert(
        patient_id=patient.id,
        alert_type="crisis",
        message=(
            f"Critical blood pressure alert for {patient.name}: "
            f"{reading.systolic:.0f}/{reading.diastolic:.0f} mmHg recorded at {reading.timestamp.isoformat()}."
        ),
        severity="critical",
        sent_via="sms",
        explanation="Rule-based alert triggered because systolic blood pressure exceeded 180 mmHg.",
    )
    db.add(alert)
    await db.flush()

    alert.sent_via = await send_alert_notifications(alert, patient)
    return alert
