"""
Alert service — decides whether to fire alerts based on ML outputs.

Logic:
- If is_anomaly == 1 AND fuzzy_severity in ["stage2", "crisis"] → fire "spike" alert
- If fuzzy_severity == "crisis" regardless of anomaly → fire "crisis" alert
- If no reading in 24 hours → fire "missed_reading" alert

Calls notification_service to actually send SMS/email.
"""

import logging
from datetime import datetime, timedelta

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bp_reading import BPReading
from app.models.alert import Alert
from app.models.patient import Patient
from app.services.notification_service import send_alert_notification

logger = logging.getLogger(__name__)


async def process_reading_for_alerts(
    session: AsyncSession,
    patient_id: int,
    bp_reading: "BPReading",
) -> Alert | None:
    """
    Evaluate a new BP reading against alert thresholds.
    Creates and sends alert if conditions are met.

    Args:
        session: AsyncSession
        patient_id: Patient ID
        bp_reading: BPReading object with ML outputs populated
                   (is_anomaly, anomaly_score, fuzzy_severity, explanation)

    Returns:
        Alert: Created alert (if any), None otherwise
    """
    alert = None

    # Threshold 1: Crisis levels (regardless of anomaly flag)
    if bp_reading.fuzzy_severity == "crisis":
        alert = await _create_and_send_crisis_alert(session, patient_id, bp_reading)

    # Threshold 2: Spike (anomaly + high severity)
    elif bp_reading.is_anomaly == 1 and bp_reading.fuzzy_severity in ["stage2", "crisis"]:
        alert = await _create_and_send_spike_alert(session, patient_id, bp_reading)

    # Threshold 3: Stage 2 sustained (not anomaly, just stage 2)
    elif not bp_reading.is_anomaly and bp_reading.fuzzy_severity == "stage2":
        # Check if already stage 2 for last 2 readings → escalate to alert
        if await _is_sustained_stage2(session, patient_id):
            alert = await _create_and_send_stage2_alert(session, patient_id, bp_reading)

    logger.info(f"Alert processing for reading {bp_reading.id}: alert_created={alert is not None}")
    return alert


async def check_missed_readings(session: AsyncSession, patient_id: int) -> Alert | None:
    """
    Check if patient has missed a reading (no reading in last 24 hours).
    Creates a "missed_reading" alert if this is the 2nd time this week.

    Args:
        session: AsyncSession
        patient_id: Patient ID

    Returns:
        Alert: Created alert (if any), None otherwise
    """
    # Get latest reading
    stmt = (
        select(BPReading)
        .where(BPReading.patient_id == patient_id)
        .order_by(desc(BPReading.timestamp))
        .limit(1)
    )
    result = await session.execute(stmt)
    latest_reading = result.scalar()

    if not latest_reading:
        logger.warning(f"Patient {patient_id} has no readings yet")
        return None

    hours_since_reading = (datetime.utcnow() - latest_reading.timestamp).total_seconds() / 3600

    if hours_since_reading > 24:
        # Count missed_reading alerts in the last 7 days
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        stmt = (
            select(Alert)
            .where(
                and_(
                    Alert.patient_id == patient_id,
                    Alert.alert_type == "missed_reading",
                    Alert.triggered_at >= seven_days_ago,
                )
            )
            .order_by(desc(Alert.triggered_at))
        )
        result = await session.execute(stmt)
        recent_missed_alerts = result.scalars().all()

        if len(recent_missed_alerts) >= 1:  # 2nd time this week
            alert = Alert(
                patient_id=patient_id,
                alert_type="missed_reading",
                message=f"No BP reading for {hours_since_reading:.1f} hours. Patient may not be checking device regularly.",
                severity="low",
                explanation=f"Last reading was {hours_since_reading:.1f} hours ago. This is the {len(recent_missed_alerts) + 1}nd missed reading alert this week.",
                sent_via="pending",
            )
            session.add(alert)
            await session.flush()

            # TODO: Decide if we notify patient for missed readings
            # For now, just log to doctor
            await send_alert_notification(session, alert, send_to_patient=False, send_to_doctor=True)
            await session.refresh(alert)

            logger.info(f"Missed reading alert created for patient {patient_id}")
            return alert

    return None


# --- Private helpers ---


async def _create_and_send_crisis_alert(
    session: AsyncSession, patient_id: int, bp_reading: "BPReading"
) -> Alert:
    """Create CRISIS alert — highest severity."""
    patient = await session.get(Patient, patient_id)

    alert = Alert(
        patient_id=patient_id,
        alert_type="crisis",
        message=f"CRITICAL: BP {bp_reading.systolic}/{bp_reading.diastolic} mmHg — Crisis levels detected. Patient requires immediate medical attention.",
        severity="critical",
        explanation=bp_reading.explanation or f"Systolic {bp_reading.systolic} exceeds crisis threshold (180). Diastolic {bp_reading.diastolic} exceeds crisis threshold (120).",
        sent_via="pending",
    )
    session.add(alert)
    await session.flush()

    # Notify both patient and doctor ASAP
    await send_alert_notification(session, alert, send_to_patient=True, send_to_doctor=True)
    await session.refresh(alert)

    logger.warning(f"🔴 CRISIS ALERT created for patient {patient_id}: {alert.message}")
    return alert


async def _create_and_send_spike_alert(
    session: AsyncSession, patient_id: int, bp_reading: "BPReading"
) -> Alert:
    """Create SPIKE alert — sudden anomalous elevation."""
    patient = await session.get(Patient, patient_id)

    # Get previous reading for comparison
    stmt = (
        select(BPReading)
        .where(BPReading.patient_id == patient_id)
        .order_by(desc(BPReading.timestamp))
        .limit(2)
    )
    result = await session.execute(stmt)
    readings = result.scalars().all()

    delta_systolic = 0
    if len(readings) >= 2:
        delta_systolic = readings[1].systolic - readings[0].systolic

    alert = Alert(
        patient_id=patient_id,
        alert_type="spike",
        message=f"BP spike detected: {bp_reading.systolic}/{bp_reading.diastolic} mmHg (anomaly score: {bp_reading.anomaly_score:.2f}). Elevated severity classification: {bp_reading.fuzzy_severity}.",
        severity="high",
        explanation=bp_reading.explanation or f"Sudden rise of {delta_systolic:.0f} mmHg from baseline. Classified as {bp_reading.fuzzy_severity}.",
        sent_via="pending",
    )
    session.add(alert)
    await session.flush()

    # Notify patient and doctor
    await send_alert_notification(session, alert, send_to_patient=True, send_to_doctor=True)
    await session.refresh(alert)

    logger.warning(f"🟠 SPIKE ALERT created for patient {patient_id} ({bp_reading.fuzzy_severity})")
    return alert


async def _create_and_send_stage2_alert(
    session: AsyncSession, patient_id: int, bp_reading: "BPReading"
) -> Alert:
    """Create STAGE2 alert — sustained stage 2 hypertension."""
    patient = await session.get(Patient, patient_id)

    alert = Alert(
        patient_id=patient_id,
        alert_type="stage2",
        message=f"BP entered Stage 2 Hypertension: {bp_reading.systolic}/{bp_reading.diastolic} mmHg. Doctor notification sent.",
        severity="medium",
        explanation=bp_reading.explanation or f"Systolic {bp_reading.systolic} >= 140 AND diastolic {bp_reading.diastolic} >= 90. Sustained stage 2 pattern detected.",
        sent_via="pending",
    )
    session.add(alert)
    await session.flush()

    # Notify doctor only for sustained stage 2
    await send_alert_notification(session, alert, send_to_patient=False, send_to_doctor=True)
    await session.refresh(alert)

    logger.warning(f"🟡 STAGE2 ALERT created for patient {patient_id}")
    return alert


async def _is_sustained_stage2(session: AsyncSession, patient_id: int) -> bool:
    """
    Check if last 2 readings are both stage 2.
    Used to avoid alerting on single stage2 blip.
    """
    stmt = (
        select(BPReading)
        .where(BPReading.patient_id == patient_id)
        .order_by(desc(BPReading.timestamp))
        .limit(2)
    )
    result = await session.execute(stmt)
    readings = result.scalars().all()

    if len(readings) < 2:
        return False

    return all(r.fuzzy_severity == "stage2" for r in readings)
