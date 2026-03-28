from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class SymptomLog(Base):
    __tablename__ = "symptom_logs"
    __table_args__ = (
        CheckConstraint("fatigue IS NULL OR fatigue BETWEEN 1 AND 10", name="ck_symptom_logs_fatigue"),
        CheckConstraint("pain_level IS NULL OR pain_level BETWEEN 1 AND 10", name="ck_symptom_logs_pain_level"),
        CheckConstraint("swelling IS NULL OR swelling BETWEEN 1 AND 10", name="ck_symptom_logs_swelling"),
        CheckConstraint("nausea IS NULL OR nausea BETWEEN 1 AND 10", name="ck_symptom_logs_nausea"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), nullable=False, index=True)
    fatigue: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pain_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    swelling: Mapped[int | None] = mapped_column(Integer, nullable=True)
    nausea: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    chat_step: Mapped[str] = mapped_column(
        String(32), nullable=False, default="start", server_default=text("'start'")
    )
    logged_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    patient = relationship("Patient", back_populates="symptom_logs")
