from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.alert import Alert
from app.models.bp_reading import BPReading
from app.models.patient import Patient
from app.models.reminder import Reminder
from app.models.symptom_log import SymptomLog

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _risk_rank(severity: str | None) -> int:
    normalized = (severity or "").lower()
    order = {
        "critical": 4,
        "stage3": 4,
        "high": 3,
        "stage2": 3,
        "medium": 2,
        "stage1": 2,
        "elevated": 1,
        "low": 1,
        "normal": 0,
    }
    return order.get(normalized, 0)


def _risk_label(severity: str | None) -> str:
    normalized = (severity or "").lower()
    if normalized in {"critical", "stage3"}:
        return "critical"
    if normalized in {"high", "stage2"}:
        return "high"
    if normalized in {"medium", "stage1", "elevated"}:
        return "medium"
    return "low"


def _serialize_reading(reading: BPReading) -> dict[str, object]:
    return {
        "id": reading.id,
        "patient_id": reading.patient_id,
        "systolic": reading.systolic,
        "diastolic": reading.diastolic,
        "timestamp": reading.timestamp.isoformat(),
        "source": reading.source,
        "anomaly_score": reading.anomaly_score,
        "is_anomaly": reading.is_anomaly,
        "fuzzy_severity": reading.fuzzy_severity,
        "explanation": reading.explanation,
    }


def _serialize_alert(alert: Alert, patient_name: str | None = None) -> dict[str, object]:
    return {
        "id": alert.id,
        "patient_id": alert.patient_id,
        "patient_name": patient_name,
        "alert_type": alert.alert_type,
        "message": alert.message,
        "severity": alert.severity,
        "sent_via": alert.sent_via,
        "triggered_at": alert.triggered_at.isoformat(),
        "explanation": alert.explanation,
    }


def _serialize_reminder(reminder: Reminder, patient_name: str | None = None) -> dict[str, object]:
    return {
        "id": reminder.id,
        "patient_id": reminder.patient_id,
        "patient_name": patient_name,
        "reminder_type": reminder.reminder_type,
        "message": reminder.message,
        "scheduled_at": reminder.scheduled_at.isoformat(),
        "sent": reminder.sent,
        "status": "sent" if reminder.sent else "pending",
    }


def _serialize_symptom(symptom: SymptomLog | None) -> dict[str, object] | None:
    if symptom is None:
        return None
    return {
        "id": symptom.id,
        "patient_id": symptom.patient_id,
        "fatigue": symptom.fatigue,
        "pain_level": symptom.pain_level,
        "swelling": symptom.swelling,
        "nausea": symptom.nausea,
        "notes": symptom.notes,
        "chat_step": symptom.chat_step,
        "logged_at": symptom.logged_at.isoformat(),
    }


@router.get("/overview")
async def get_dashboard_overview(db: AsyncSession = Depends(get_db)) -> dict[str, object]:
    patients_result = await db.execute(select(Patient).order_by(Patient.created_at.desc(), Patient.id.desc()))
    patients = list(patients_result.scalars().all())

    readings_result = await db.execute(
        select(BPReading).order_by(BPReading.patient_id.asc(), BPReading.timestamp.desc(), BPReading.id.desc())
    )
    alerts_result = await db.execute(
        select(Alert).order_by(Alert.patient_id.asc(), Alert.triggered_at.desc(), Alert.id.desc())
    )

    latest_reading_by_patient: dict[int, BPReading] = {}
    for reading in readings_result.scalars().all():
        latest_reading_by_patient.setdefault(reading.patient_id, reading)

    latest_alert_by_patient: dict[int, Alert] = {}
    all_alerts = list(alerts_result.scalars().all())
    for alert in all_alerts:
        latest_alert_by_patient.setdefault(alert.patient_id, alert)

    rows: list[dict[str, object]] = []
    for patient in patients:
        latest_reading = latest_reading_by_patient.get(patient.id)
        latest_alert = latest_alert_by_patient.get(patient.id)
        risk_source = None
        if latest_alert is not None:
            risk_source = latest_alert.severity
        elif latest_reading is not None:
            risk_source = latest_reading.fuzzy_severity

        rows.append(
            {
                "id": patient.id,
                "name": patient.name,
                "email": patient.email,
                "phone": patient.phone,
                "age": patient.age,
                "ckd_stage": patient.ckd_stage,
                "risk_level": _risk_label(risk_source),
                "risk_rank": _risk_rank(risk_source),
                "latest_bp": f"{int(latest_reading.systolic)}/{int(latest_reading.diastolic)}" if latest_reading else None,
                "latest_reading_at": latest_reading.timestamp.isoformat() if latest_reading else None,
                "active_today": latest_reading is not None,
                "anomaly_status": "Anomaly" if latest_reading and latest_reading.is_anomaly else "Normal",
                "anomaly_score": latest_reading.anomaly_score if latest_reading else None,
                "summary": latest_reading.explanation if latest_reading else None,
            }
        )

    critical_count = sum(1 for row in rows if row["risk_level"] == "critical")
    high_count = sum(1 for row in rows if row["risk_level"] == "high")
    active_count = sum(1 for row in rows if row["active_today"])

    rows.sort(key=lambda row: (-int(row["risk_rank"]), row["name"]))
    for row in rows:
        row.pop("risk_rank", None)

    return {
        "kpis": {
            "total_patients": len(rows),
            "critical_risk": critical_count,
            "high_risk": high_count,
            "active_today": active_count,
        },
        "patients": rows,
    }


@router.get("/patients/{patient_id}")
async def get_dashboard_patient(patient_id: int, db: AsyncSession = Depends(get_db)) -> dict[str, object]:
    patient = await db.get(Patient, patient_id)
    if patient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    readings_result = await db.execute(
        select(BPReading)
        .where(BPReading.patient_id == patient_id)
        .order_by(BPReading.timestamp.desc(), BPReading.id.desc())
    )
    alerts_result = await db.execute(
        select(Alert)
        .where(Alert.patient_id == patient_id)
        .order_by(Alert.triggered_at.desc(), Alert.id.desc())
    )
    reminders_result = await db.execute(
        select(Reminder)
        .where(Reminder.patient_id == patient_id)
        .order_by(Reminder.scheduled_at.desc(), Reminder.id.desc())
    )
    symptom_result = await db.execute(
        select(SymptomLog)
        .where(SymptomLog.patient_id == patient_id)
        .order_by(SymptomLog.logged_at.desc(), SymptomLog.id.desc())
        .limit(1)
    )

    readings = list(readings_result.scalars().all())
    alerts = list(alerts_result.scalars().all())
    reminders = list(reminders_result.scalars().all())
    symptom = symptom_result.scalar_one_or_none()
    latest_reading = readings[0] if readings else None
    latest_alert = alerts[0] if alerts else None
    risk_source = latest_alert.severity if latest_alert else (latest_reading.fuzzy_severity if latest_reading else None)

    return {
        "patient": {
            "id": patient.id,
            "name": patient.name,
            "email": patient.email,
            "phone": patient.phone,
            "age": patient.age,
            "ckd_stage": patient.ckd_stage,
            "risk_level": _risk_label(risk_source),
            "latest_bp": f"{int(latest_reading.systolic)}/{int(latest_reading.diastolic)}" if latest_reading else None,
            "latest_reading_at": latest_reading.timestamp.isoformat() if latest_reading else None,
            "anomaly_status": "Anomaly" if latest_reading and latest_reading.is_anomaly else "Normal",
            "anomaly_score": latest_reading.anomaly_score if latest_reading else None,
            "summary": latest_reading.explanation if latest_reading else None,
            "clinical_explanation": alerts[0].explanation if alerts else latest_reading.explanation if latest_reading else None,
        },
        "readings": [_serialize_reading(reading) for reading in readings],
        "alerts": [_serialize_alert(alert, patient.name) for alert in alerts],
        "reminders": [_serialize_reminder(reminder, patient.name) for reminder in reminders],
        "symptom_log": _serialize_symptom(symptom),
    }


@router.get("/alerts")
async def get_dashboard_alerts(db: AsyncSession = Depends(get_db)) -> dict[str, object]:
    result = await db.execute(
        select(Alert, Patient.name)
        .join(Patient, Patient.id == Alert.patient_id)
        .order_by(Alert.triggered_at.desc(), Alert.id.desc())
    )
    rows = [_serialize_alert(alert, patient_name) for alert, patient_name in result.all()]
    return {
        "kpis": {
            "critical": sum(1 for row in rows if str(row["severity"]).lower() == "critical"),
            "high": sum(1 for row in rows if str(row["severity"]).lower() == "high"),
            "unresolved": len(rows),
            "today": len(rows),
        },
        "alerts": rows,
    }


@router.get("/reminders")
async def get_dashboard_reminders(db: AsyncSession = Depends(get_db)) -> dict[str, object]:
    result = await db.execute(
        select(Reminder, Patient.name)
        .join(Patient, Patient.id == Reminder.patient_id)
        .order_by(Reminder.scheduled_at.desc(), Reminder.id.desc())
    )
    rows = [_serialize_reminder(reminder, patient_name) for reminder, patient_name in result.all()]
    return {
        "kpis": {
            "due_today": len(rows),
            "sent": sum(1 for row in rows if row["sent"]),
            "pending": sum(1 for row in rows if not row["sent"]),
            "active": sum(1 for row in rows if not row["sent"]),
        },
        "reminders": rows,
    }
