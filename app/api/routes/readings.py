from fastapi import APIRouter
from app.schemas.bp_reading import BPReadingCreate

# Note: Using an in-memory list since Step 5 does not require a fully working PostgreSQL DB yet.
# Step 1 (DB Models) needs to be implemented by other teammates before we can inject an SQLAlchemy session here.
MOCK_DATABASE = []

router = APIRouter()

@router.post("/")
async def ingest_reading(reading: BPReadingCreate):
    print(f"RECEIVED BP READING: Systolic {reading.systolic}, Diastolic {reading.diastolic} at {reading.timestamp} from {reading.source}")
    # In a real scenario, this would interact with db_session to INSERT into bp_readings and call ml/anomaly.py
    # For Step 5 testing, we append to an in-memory mock to confirm the pipeline works.
    record = reading.model_dump()
    record["id"] = len(MOCK_DATABASE) + 1
    MOCK_DATABASE.append(record)
    
    return {"status": "success", "message": "Reading ingested via Step 5 pipeline", "data": record}

@router.get("/{patient_id}")
async def get_patient_readings(patient_id: int):
    return [r for r in MOCK_DATABASE if r.get("patient_id") == patient_id]
