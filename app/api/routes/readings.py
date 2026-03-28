from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.bp_reading import BPReading
from app.models.patient import Patient
from app.schemas.bp_reading import BPReadingCreate, BPReadingRead
from app.services.alert_service import evaluate_reading_for_alerts


router = APIRouter(prefix="/readings", tags=["readings"])


async def _get_patient_or_404(patient_id: int, db: AsyncSession) -> Patient:
    patient = await db.get(Patient, patient_id)
    if patient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    return patient


@router.post("/", response_model=BPReadingRead, status_code=status.HTTP_201_CREATED)
async def create_reading(payload: BPReadingCreate, db: AsyncSession = Depends(get_db)) -> BPReading:
    patient = await _get_patient_or_404(payload.patient_id, db)

    reading = BPReading(**payload.model_dump())
    db.add(reading)
    await db.flush()

    await evaluate_reading_for_alerts(reading, patient, db)

    await db.commit()
    await db.refresh(reading)
    return reading


@router.get("/{patient_id}", response_model=list[BPReadingRead])
async def list_readings(patient_id: int, db: AsyncSession = Depends(get_db)) -> list[BPReading]:
    await _get_patient_or_404(patient_id, db)
    result = await db.execute(
        select(BPReading)
        .where(BPReading.patient_id == patient_id)
        .order_by(BPReading.timestamp.desc(), BPReading.id.desc())
    )
    return list(result.scalars().all())


@router.get("/{patient_id}/latest", response_model=BPReadingRead)
async def get_latest_reading(patient_id: int, db: AsyncSession = Depends(get_db)) -> BPReading:
    await _get_patient_or_404(patient_id, db)
    result = await db.execute(
        select(BPReading)
        .where(BPReading.patient_id == patient_id)
        .order_by(BPReading.timestamp.desc(), BPReading.id.desc())
        .limit(1)
    )
    reading = result.scalar_one_or_none()
    if reading is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No readings found for patient")
    return reading
