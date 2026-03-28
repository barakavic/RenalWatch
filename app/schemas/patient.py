from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PatientBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    phone: str = Field(..., min_length=10, max_length=32)
    email: str | None = Field(default=None, max_length=255)
    age: int = Field(..., ge=1, le=130)
    ckd_stage: int = Field(..., ge=1, le=5)


class PatientCreate(PatientBase):
    pass


class PatientUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    phone: str | None = Field(default=None, min_length=10, max_length=32)
    email: str | None = Field(default=None, max_length=255)
    age: int | None = Field(default=None, ge=1, le=130)
    ckd_stage: int | None = Field(default=None, ge=1, le=5)


class PatientRead(PatientBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
