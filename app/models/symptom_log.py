from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class SymptomLog(Base):
    __tablename__ = "symptom_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), nullable=False, index=True)
    fatigue: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pain_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    swelling: Mapped[int | None] = mapped_column(Integer, nullable=True)
    nausea: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    chat_step: Mapped[str] = mapped_column(String(32), nullable=False, default="start")
    logged_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    patient = relationship("Patient", back_populates="symptom_logs")
