from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ml.anomaly import detect
from app.ml.explain import build_explanations
from app.ml.rules import classify_bp
from app.models.alert import Alert
from app.models.bp_reading import BPReading
from app.models.patient import Patient
from app.services.notification_service import send_alert_notifications


async def evaluate_reading_for_alerts(reading: BPReading, patient: Patient, db: AsyncSession) -> Alert | None:
    history_result = await db.execute(
        select(BPReading)
        .where(BPReading.patient_id == patient.id, BPReading.id != reading.id)
        .order_by(BPReading.timestamp.desc(), BPReading.id.desc())
        .limit(5)
    )
    history_rows = list(history_result.scalars().all())
    history = [{"systolic": row.systolic, "diastolic": row.diastolic} for row in history_rows]

    anomaly_result = detect(
        systolic=reading.systolic,
        diastolic=reading.diastolic,
        history=history,
    )
    rule_result = classify_bp(reading.systolic, reading.diastolic)
    explanation_result = build_explanations(
        systolic=reading.systolic,
        diastolic=reading.diastolic,
        anomaly_result=anomaly_result,
        rule_result=rule_result,
    )

    reading.anomaly_score = anomaly_result["anomaly_score"]
    reading.is_anomaly = 1 if anomaly_result["is_anomaly"] else 0
    reading.fuzzy_severity = rule_result["severity"]
    reading.explanation = explanation_result["summary"]

    alert_type: str | None = None
    severity: str | None = None
    explanation: str | None = None

    if reading.fuzzy_severity == "crisis" or reading.systolic > 180 or reading.diastolic > 120:
        alert_type = "crisis"
        severity = "critical"
        explanation = explanation_result["doctor_explanation"] or "Rule-based alert triggered because blood pressure exceeded crisis threshold."
    elif reading.is_anomaly == 1 and reading.fuzzy_severity in {"stage2", "crisis"}:
        alert_type = "spike"
        severity = "high"
        explanation = explanation_result["doctor_explanation"] or "Anomalous spike detected together with elevated severity."
    elif reading.fuzzy_severity == "stage2" or reading.systolic >= 140 or reading.diastolic >= 90:
        alert_type = "stage2"
        severity = "high"
        explanation = explanation_result["doctor_explanation"] or "Rule-based alert triggered because blood pressure reached Stage 2 threshold."

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
