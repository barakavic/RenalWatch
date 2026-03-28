import asyncio
from datetime import UTC, datetime
import os
import sys

from sqlalchemy import select
from sqlalchemy.orm import selectinload

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import AsyncSessionLocal
from app.models.patient import Patient
from app.models.reminder import Reminder
from app.services.notification_service import send_reminder_notification


POLL_INTERVAL_SECONDS = 60


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _scheduled_datetime(now: datetime, hour: int, minute: int = 0) -> datetime:
    return now.replace(hour=hour, minute=minute, second=0, microsecond=0)


def _build_daily_message(patient: Patient, reminder_type: str) -> str:
    if reminder_type == "medication":
        return f"Time to take your medication, {patient.name}."
    if reminder_type == "bp_check":
        return "Please take your BP reading for today."
    return "Your doctor check-in is due. Open the app to log symptoms."


async def seed_due_reminders() -> None:
    now = _utc_now()

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Patient).order_by(Patient.id.asc()))
        patients = list(result.scalars().all())

        if not patients:
            return

        reminder_specs = [
            ("medication", _scheduled_datetime(now, 8)),
            ("bp_check", _scheduled_datetime(now, 18)),
        ]

        if now.weekday() == 0:
            reminder_specs.append(("appointment", _scheduled_datetime(now, 9)))

        for patient in patients:
            for reminder_type, scheduled_at in reminder_specs:
                exists_result = await db.execute(
                    select(Reminder).where(
                        Reminder.patient_id == patient.id,
                        Reminder.reminder_type == reminder_type,
                        Reminder.scheduled_at == scheduled_at,
                    )
                )
                existing = exists_result.scalar_one_or_none()
                if existing is not None:
                    continue

                db.add(
                    Reminder(
                        patient_id=patient.id,
                        reminder_type=reminder_type,
                        message=_build_daily_message(patient, reminder_type),
                        scheduled_at=scheduled_at,
                        sent=0,
                    )
                )

        await db.commit()


async def dispatch_due_reminders() -> int:
    now = _utc_now()

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Reminder)
            .options(selectinload(Reminder.patient))
            .where(Reminder.sent == 0, Reminder.scheduled_at <= now)
            .order_by(Reminder.scheduled_at.asc(), Reminder.id.asc())
        )
        reminders = list(result.scalars().all())

        sent_count = 0
        for reminder in reminders:
            await send_reminder_notification(reminder, reminder.patient)
            reminder.sent = 1
            sent_count += 1

        if sent_count:
            await db.commit()

        return sent_count


async def run_scheduler() -> None:
    while True:
        try:
            await seed_due_reminders()
            await dispatch_due_reminders()
        except Exception as exc:
            print(f"[scheduler] iteration failed: {exc}")

        await asyncio.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    asyncio.run(run_scheduler())
