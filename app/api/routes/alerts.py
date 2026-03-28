from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.alert import Alert
from app.models.patient import Patient


router = APIRouter(prefix="/alerts", tags=["alerts"])


def _serialize_alert(alert: Alert) -> dict[str, str | int]:
    return {
        "id": alert.id,
        "patient_id": alert.patient_id,
        "alert_type": alert.alert_type,
        "message": alert.message,
        "severity": alert.severity,
        "sent_via": alert.sent_via,
        "triggered_at": alert.triggered_at.isoformat(),
        "explanation": alert.explanation,
    }


@router.get("/{patient_id}")
async def list_alerts(patient_id: int, db: AsyncSession = Depends(get_db)) -> list[dict[str, str | int]]:
    patient = await db.get(Patient, patient_id)
    if patient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    result = await db.execute(
        select(Alert).where(Alert.patient_id == patient_id).order_by(Alert.triggered_at.desc(), Alert.id.desc())
    )
    alerts = list(result.scalars().all())
    return [_serialize_alert(alert) for alert in alerts]
