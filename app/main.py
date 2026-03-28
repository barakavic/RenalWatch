from fastapi import FastAPI
from app.api.routes import readings
# Other routes (patients, alerts, dashboard) left out intentionally for now since it is not my step.

app = FastAPI(title="RenalWatch API", description="Test Endpoint for Step 5 (ADB worker)")

# Include routers
app.include_router(readings.router, prefix="/readings", tags=["readings"])

@app.get("/")
def root():
    return {"message": "Welcome to RenalWatch API (Step 5 Sandbox)"}
