import logging
from fastapi import APIRouter, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services.chatbot_service import process_whatsapp_message

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chatbot", tags=["chatbot"])


@router.get("/webhook")
async def chatbot_webhook_status() -> dict[str, str]:
    return {"status": "ready"}

@router.post("/webhook")
async def chatbot_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Africa's Talking WhatsApp / SMS Webhook
    Receives Form Data (application/x-www-form-urlencoded).
    """
    form_data = await request.form()
    
    sender = (
        form_data.get("From")
        or form_data.get("from")
        or form_data.get("WaId")
        or form_data.get("phoneNumber")
        or form_data.get("phone")
        or form_data.get("sender")
    )
    text = (
        form_data.get("Body")
        or form_data.get("text")
        or form_data.get("body")
        or form_data.get("message")
        or ""
    )
    
    sender = sender.removeprefix("whatsapp:") if sender else sender

    logger.info("Chatbot incoming message: sender=%s text=%s", sender, text)
    
    if sender and text is not None:
        # We process this in the background or await it 
        # AT expects a quick 200 OK response from your server wrapper
        # To avoid timeout, we can handle it directly or via BackgroundTasks.
        # Since it's a simple state machine, awaiting it directly here is fine.
        await process_whatsapp_message(sender, text, db)
    else:
        logger.warning("Chatbot webhook ignored: sender=%s text=%s", sender, text)
        
    return {"status": "success"}
