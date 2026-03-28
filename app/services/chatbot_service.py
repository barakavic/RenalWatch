import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.patient import Patient
from app.models.symptom_log import SymptomLog
from app.integrations.africas_talking import send_whatsapp_message
from app.services.notification_service import notify_doctor_symptoms

logger = logging.getLogger(__name__)

async def process_whatsapp_message(phone: str, text: str, db: AsyncSession):
    """
    State machine for WhatsApp chatbot check-in.
    """
    text = text.strip()
    
    # 1. Look up patient by phone
    stmt = select(Patient).where(Patient.phone == phone)
    result = await db.execute(stmt)
    patient = result.scalars().first()
    
    if not patient:
        send_whatsapp_message(phone, "Sorry, your phone number is not registered for RenalWatch monitoring.")
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
    
    # Parse integer if the response is a rating (1-10)
    try:
        val = int(text)
    except ValueError:
        val = None
        
    if step == "start":
        reply_message = f"Hi {patient.name}, time for your weekly check-in. How are you feeling? Rate your energy/fatigue (1-10, where 10 is very bad)."
        active_log.chat_step = "fatigue"
        
    elif step == "fatigue":
        if val is None or not (1 <= val <= 10):
            reply_message = "Please reply with a number between 1 and 10 for fatigue."
        else:
            active_log.fatigue = val
            active_log.chat_step = "pain"
            reply_message = "Thanks. Any pain today? Rate 1-10 (10 being severe pain)."
            
    elif step == "pain":
        if val is None or not (1 <= val <= 10):
            reply_message = "Please reply with a number between 1 and 10 for pain."
        else:
            active_log.pain_level = val
            active_log.chat_step = "swelling"
            reply_message = "Any swelling in your legs or ankles? Rate 1-10."
            
    elif step == "swelling":
        if val is None or not (1 <= val <= 10):
            reply_message = "Please reply with a number between 1 and 10 for swelling."
        else:
            active_log.swelling = val
            active_log.chat_step = "nausea"
            reply_message = "Feeling nauseous at all? Rate 1-10."
            
    elif step == "nausea":
        if val is None or not (1 <= val <= 10):
            reply_message = "Please reply with a number between 1 and 10 for nausea."
        else:
            active_log.nausea = val
            active_log.chat_step = "notes"
            reply_message = "Anything else you'd like to tell your doctor?"
            
    elif step == "notes":
        active_log.notes = text
        active_log.chat_step = "done"
        reply_message = "Thank you. Your doctor has been notified. Take care!"
        # notify doctor
        await notify_doctor_symptoms(patient, active_log)

    await db.commit()
    
    # Send reply via integration
    send_whatsapp_message(phone, reply_message)
