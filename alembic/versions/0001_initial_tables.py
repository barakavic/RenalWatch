"""initial tables

Revision ID: 0001_initial_tables
Revises:
Create Date: 2026-03-28 15:40:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0001_initial_tables"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "patients",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=32), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("age", sa.Integer(), nullable=False),
        sa.Column("ckd_stage", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(op.f("ix_patients_id"), "patients", ["id"], unique=False)
    op.create_index(op.f("ix_patients_phone"), "patients", ["phone"], unique=True)

    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("alert_type", sa.String(length=32), nullable=False),
        sa.Column("message", sa.String(length=1024), nullable=False),
        sa.Column("severity", sa.String(length=32), nullable=False),
        sa.Column("sent_via", sa.String(length=32), nullable=False),
        sa.Column("triggered_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("explanation", sa.String(length=1024), nullable=False),
    )
    op.create_index(op.f("ix_alerts_id"), "alerts", ["id"], unique=False)
    op.create_index(op.f("ix_alerts_patient_id"), "alerts", ["patient_id"], unique=False)

    op.create_table(
        "bp_readings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("systolic", sa.Float(), nullable=False),
        sa.Column("diastolic", sa.Float(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("anomaly_score", sa.Float(), nullable=True),
        sa.Column("is_anomaly", sa.Integer(), nullable=False),
        sa.Column("fuzzy_severity", sa.String(length=32), nullable=True),
        sa.Column("explanation", sa.String(length=1024), nullable=True),
    )
    op.create_index(op.f("ix_bp_readings_id"), "bp_readings", ["id"], unique=False)
    op.create_index(op.f("ix_bp_readings_patient_id"), "bp_readings", ["patient_id"], unique=False)
    op.create_index(op.f("ix_bp_readings_timestamp"), "bp_readings", ["timestamp"], unique=False)

    op.create_table(
        "reminders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("reminder_type", sa.String(length=32), nullable=False),
        sa.Column("message", sa.String(length=1024), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sent", sa.Integer(), nullable=False),
    )
    op.create_index(op.f("ix_reminders_id"), "reminders", ["id"], unique=False)
    op.create_index(op.f("ix_reminders_patient_id"), "reminders", ["patient_id"], unique=False)

    op.create_table(
        "symptom_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("fatigue", sa.Integer(), nullable=True),
        sa.Column("pain_level", sa.Integer(), nullable=True),
        sa.Column("swelling", sa.Integer(), nullable=True),
        sa.Column("nausea", sa.Integer(), nullable=True),
        sa.Column("notes", sa.String(length=1024), nullable=True),
        sa.Column("chat_step", sa.String(length=32), nullable=False),
        sa.Column("logged_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(op.f("ix_symptom_logs_id"), "symptom_logs", ["id"], unique=False)
    op.create_index(op.f("ix_symptom_logs_patient_id"), "symptom_logs", ["patient_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_symptom_logs_patient_id"), table_name="symptom_logs")
    op.drop_index(op.f("ix_symptom_logs_id"), table_name="symptom_logs")
    op.drop_table("symptom_logs")

    op.drop_index(op.f("ix_reminders_patient_id"), table_name="reminders")
    op.drop_index(op.f("ix_reminders_id"), table_name="reminders")
    op.drop_table("reminders")

    op.drop_index(op.f("ix_bp_readings_timestamp"), table_name="bp_readings")
    op.drop_index(op.f("ix_bp_readings_patient_id"), table_name="bp_readings")
    op.drop_index(op.f("ix_bp_readings_id"), table_name="bp_readings")
    op.drop_table("bp_readings")

    op.drop_index(op.f("ix_alerts_patient_id"), table_name="alerts")
    op.drop_index(op.f("ix_alerts_id"), table_name="alerts")
    op.drop_table("alerts")

    op.drop_index(op.f("ix_patients_phone"), table_name="patients")
    op.drop_index(op.f("ix_patients_id"), table_name="patients")
    op.drop_table("patients")
