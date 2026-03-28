from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# Import models so Alembic sees them when loading Base.metadata.
from app.models.alert import Alert  # noqa: E402,F401
from app.models.bp_reading import BPReading  # noqa: E402,F401
from app.models.patient import Patient  # noqa: E402,F401
from app.models.reminder import Reminder  # noqa: E402,F401
from app.models.symptom_log import SymptomLog  # noqa: E402,F401
