import logging
from fastapi import APIRouter, Request, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services.chatbot_service import process_whatsapp_message

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chatbot", tags=["chatbot"])

@router.post("/webhook")
async def africas_talking_webhook(
    request: Request, 
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Africa's Talking WhatsApp / SMS Webhook
    Receives Form Data (application/x-www-form-urlencoded).
    """
    form_data = await request.form()
    
    sender = form_data.get("from")
    text = form_data.get("text")
    
    logger.info(f"Received webhook from AT: sender={sender}, text={text}")
    
    if sender and text is not None:
        # We process this in the background or await it 
        # AT expects a quick 200 OK response from your server wrapper
        # To avoid timeout, we can handle it directly or via BackgroundTasks.
        # Since it's a simple state machine, awaiting it directly here is fine.
        await process_whatsapp_message(sender, text, db)
        
    return {"status": "success"}
