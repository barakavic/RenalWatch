import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.nlp.formatter import (
    format_checkin_prompt,
    format_completion_message,
    format_help_message,
    format_invalid_rating,
)
from app.nlp.chat_engine import (
    apply_symptom_ratings,
    generate_model_followup,
    is_model_available,
    reset_chat_session,
    start_model_checkin,
)
from app.nlp.parser import parse_chat_message
from app.models.patient import Patient
from app.models.symptom_log import SymptomLog
from app.core.config import settings
from app.integrations.africas_talking import send_whatsapp_message as send_at_whatsapp_message
from app.integrations.twilio_whatsapp import send_whatsapp_message as send_twilio_whatsapp_message
from app.services.notification_service import notify_doctor_symptoms

logger = logging.getLogger(__name__)


def _normalize_phone(phone: str | None) -> str | None:
    if not phone:
        return None

    normalized = phone.strip().removeprefix("whatsapp:").replace(" ", "")
    if normalized.startswith("0") and len(normalized) == 10:
        normalized = f"+254{normalized[1:]}"
    elif normalized.startswith("254") and not normalized.startswith("+254"):
        normalized = f"+{normalized}"
    return normalized


def _send_chat_reply(phone: str, message: str) -> None:
    logger.info("Chatbot outgoing reply: phone=%s message=%s", phone, message)
    if settings.whatsapp_provider.lower() == "twilio":
        send_twilio_whatsapp_message(phone, message)
        return
    send_at_whatsapp_message(phone, message)

async def process_whatsapp_message(phone: str, text: str, db: AsyncSession):
    """
    State machine for WhatsApp chatbot check-in.
    """
    phone = _normalize_phone(phone)
    text = text.strip()
    parsed = parse_chat_message(text)
    logger.info("Chatbot processing: normalized_phone=%s text=%s parsed=%s", phone, text, parsed)
    
    # 1. Look up patient by phone
    stmt = select(Patient)
    result = await db.execute(stmt)
    patient = None
    for candidate in result.scalars().all():
        if _normalize_phone(candidate.phone) == phone:
            patient = candidate
            break
    
    if not patient:
        logger.warning("Chatbot patient lookup failed: phone=%s", phone)
        _send_chat_reply(phone, "Sorry, your phone number is not registered for RenalWatch monitoring.")
        return
    logger.info("Chatbot patient matched: patient_id=%s name=%s phone=%s", patient.id, patient.name, patient.phone)

    if is_model_available():
        await _process_model_message(patient, phone, text, db)
        return
        
    # 2. Check for active check-in
    log_stmt = select(SymptomLog).where(
        SymptomLog.patient_id == patient.id,
        SymptomLog.chat_step != "done"
    ).order_by(SymptomLog.logged_at.desc())
    
    log_result = await db.execute(log_stmt)
    active_log = log_result.scalars().first()
    
    if not active_log:
        logger.info(f"Chatbot Service: Starting new symptom log for {patient.name}")
        active_log = SymptomLog(patient_id=patient.id, chat_step="start")
        db.add(active_log)
    
    reply_message = ""
    step = active_log.chat_step
    logger.info("Chatbot current step: patient_id=%s log_id=%s step=%s", patient.id, active_log.id, step)
    
    val = parsed["number"]

    if step != "start" and parsed["is_help"]:
        logger.info("Chatbot help requested: patient_id=%s step=%s", patient.id, step)
        _send_chat_reply(phone, format_help_message(step))
        return
        
    if step == "start":
        reply_message = format_checkin_prompt("start", patient.name)
        active_log.chat_step = "fatigue"
        
    elif step == "fatigue":
        if val is None or not (1 <= val <= 10):
            if parsed["is_greeting"]:
                reply_message = format_checkin_prompt("start", patient.name)
            else:
                reply_message = format_invalid_rating("fatigue")
        else:
            active_log.fatigue = val
            active_log.chat_step = "pain"
            reply_message = format_checkin_prompt("fatigue", patient.name)
            
    elif step == "pain":
        if val is None or not (1 <= val <= 10):
            reply_message = format_invalid_rating("pain")
        else:
            active_log.pain_level = val
            active_log.chat_step = "swelling"
            reply_message = format_checkin_prompt("pain", patient.name)
            
    elif step == "swelling":
        if val is None or not (1 <= val <= 10):
            reply_message = format_invalid_rating("swelling")
        else:
            active_log.swelling = val
            active_log.chat_step = "nausea"
            reply_message = format_checkin_prompt("swelling", patient.name)
            
    elif step == "nausea":
        if val is None or not (1 <= val <= 10):
            reply_message = format_invalid_rating("nausea")
        else:
            active_log.nausea = val
            active_log.chat_step = "notes"
            reply_message = format_checkin_prompt("nausea", patient.name)
            
    elif step == "notes":
        active_log.notes = None if parsed["normalized"] in {"none", "no", "nothing"} else text
        active_log.chat_step = "done"
        reply_message = format_completion_message(patient.name)
        # notify doctor
        await notify_doctor_symptoms(patient, active_log)

    await db.commit()
    logger.info(
        "Chatbot step committed: patient_id=%s log_id=%s next_step=%s fatigue=%s pain=%s swelling=%s nausea=%s",
        patient.id,
        active_log.id,
        active_log.chat_step,
        active_log.fatigue,
        active_log.pain_level,
        active_log.swelling,
        active_log.nausea,
    )
    
    # Send reply via integration
    _send_chat_reply(phone, reply_message)


async def _process_model_message(patient: Patient, phone: str, text: str, db: AsyncSession) -> None:
    log_stmt = select(SymptomLog).where(
        SymptomLog.patient_id == patient.id,
        SymptomLog.chat_step != "done"
    ).order_by(SymptomLog.logged_at.desc())

    log_result = await db.execute(log_stmt)
    active_log = log_result.scalars().first()

    if not active_log:
        active_log = SymptomLog(patient_id=patient.id, chat_step="model")
        db.add(active_log)
        start_model_checkin(patient.name, phone)
        logger.info("Model chatbot started new conversation: patient_id=%s", patient.id)

    result = generate_model_followup(patient.name, phone, text)
    apply_symptom_ratings(active_log, result["symptom_ratings"])
    active_log.notes = result["summary"]
    active_log.chat_step = "done" if result["done"] else "model"

    if result["done"] or result["escalate"]:
        await notify_doctor_symptoms(patient, active_log)
        if result["done"]:
            reset_chat_session(phone)

    await db.commit()
    logger.info(
        "Model chatbot step committed: patient_id=%s log_id=%s step=%s summary=%s",
        patient.id,
        active_log.id,
        active_log.chat_step,
        active_log.notes,
    )
    _send_chat_reply(phone, result["reply"])
