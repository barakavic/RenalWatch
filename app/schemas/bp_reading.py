from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class BPReadingCreate(BaseModel):
    patient_id: Optional[int] = 1 # Default to 1 for MVP testing purposes
    systolic: float
    diastolic: float
    timestamp: datetime
    source: str = "wearable"
