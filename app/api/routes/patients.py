from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.patient import Patient
from app.schemas.patient import PatientCreate, PatientRead, PatientUpdate


router = APIRouter(prefix="/patients", tags=["patients"])


async def _get_patient_or_404(patient_id: int, db: AsyncSession) -> Patient:
    patient = await db.get(Patient, patient_id)
    if patient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    return patient


@router.post("/", response_model=PatientRead, status_code=status.HTTP_201_CREATED)
async def create_patient(payload: PatientCreate, db: AsyncSession = Depends(get_db)) -> Patient:
    patient = Patient(**payload.model_dump())
    db.add(patient)

    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A patient with that phone number already exists",
        ) from exc

    await db.refresh(patient)
    return patient


@router.get("/", response_model=list[PatientRead])
async def list_patients(db: AsyncSession = Depends(get_db)) -> list[Patient]:
    result = await db.execute(select(Patient).order_by(Patient.created_at.desc(), Patient.id.desc()))
    return list(result.scalars().all())


@router.get("/{patient_id}", response_model=PatientRead)
async def get_patient(patient_id: int, db: AsyncSession = Depends(get_db)) -> Patient:
    return await _get_patient_or_404(patient_id, db)


@router.put("/{patient_id}", response_model=PatientRead)
async def update_patient(
    patient_id: int, payload: PatientUpdate, db: AsyncSession = Depends(get_db)
) -> Patient:
    patient = await _get_patient_or_404(patient_id, db)

    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(patient, field, value)

    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A patient with that phone number already exists",
        ) from exc

    await db.refresh(patient)
    return patient
