from fastapi import FastAPI

from app.api.routes.alerts import router as alerts_router
from app.api.routes.chatbot import router as chatbot_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.patients import router as patients_router
from app.api.routes.readings import router as readings_router
from app.core.config import settings


app = FastAPI(title=settings.app_name, debug=settings.debug)

app.include_router(patients_router)
app.include_router(readings_router)
app.include_router(alerts_router)
app.include_router(chatbot_router)
app.include_router(dashboard_router)


@app.get("/", tags=["health"])
async def root() -> dict[str, str]:
    return {"message": "RenalWatch API is running"}


@app.get("/health", tags=["health"])
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
