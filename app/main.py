import threading

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.alerts import router as alerts_router
from app.api.routes.chatbot import router as chatbot_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.patients import router as patients_router
from app.api.routes.readings import router as readings_router
from app.core.config import settings
from app.nlp.chat_engine import warm_chat_model


app = FastAPI(title=settings.app_name, debug=settings.debug)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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


@app.on_event("startup")
async def preload_chatbot_model() -> None:
    thread = threading.Thread(target=warm_chat_model, daemon=True)
    thread.start()
