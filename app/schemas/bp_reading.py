from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BPReadingCreate(BaseModel):
    patient_id: int = Field(..., ge=1)
    systolic: float = Field(..., ge=1)
    diastolic: float = Field(..., ge=1)
    timestamp: datetime
    source: str = Field(default="wearable", min_length=1, max_length=32)


class BPReadingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int
    systolic: float
    diastolic: float
    timestamp: datetime
    source: str
    anomaly_score: float | None
    is_anomaly: int
    fuzzy_severity: str | None
    explanation: str | None
