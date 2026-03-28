from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert
from app.models.bp_reading import BPReading
from app.models.patient import Patient
from app.services.notification_service import send_alert_notifications


async def evaluate_reading_for_alerts(reading: BPReading, patient: Patient, db: AsyncSession) -> Alert | None:
    alert_type: str | None = None
    severity: str | None = None
    explanation: str | None = None

    if reading.fuzzy_severity == "crisis" or reading.systolic > 180 or reading.diastolic > 120:
        alert_type = "crisis"
        severity = "critical"
        explanation = reading.explanation or "Rule-based alert triggered because blood pressure exceeded crisis threshold."
    elif reading.is_anomaly == 1 and reading.fuzzy_severity in {"stage2", "crisis"}:
        alert_type = "spike"
        severity = "high"
        explanation = reading.explanation or "Anomalous spike detected together with elevated severity."
    elif reading.fuzzy_severity == "stage2" or reading.systolic >= 140 or reading.diastolic >= 90:
        alert_type = "stage2"
        severity = "high"
        explanation = reading.explanation or "Rule-based alert triggered because blood pressure reached Stage 2 threshold."

    if alert_type is None or severity is None or explanation is None:
        return None

    alert = Alert(
        patient_id=patient.id,
        alert_type=alert_type,
        message=(
            f"Blood pressure alert for {patient.name}: "
            f"{reading.systolic:.0f}/{reading.diastolic:.0f} mmHg recorded at {reading.timestamp.isoformat()}."
        ),
        severity=severity,
        sent_via="none",
        explanation=explanation,
    )
    db.add(alert)
    await db.flush()

    alert.sent_via = await send_alert_notifications(alert, patient)
    return alert
