from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import crud, schemas
from ..database import get_db
from ..message_handler import handle_incoming_message

router = APIRouter(prefix="/api/messages", tags=["messages"])


@router.post("/manual")
async def manual_message(payload: schemas.ManualMessageIn, db: Session = Depends(get_db)):
    """Ручной ввод сообщения из WhatsApp или MAX."""
    reply = await handle_incoming_message(
        db=db,
        channel=payload.channel,
        sender_id=payload.sender_id,
        text=payload.text,
        phone=payload.phone,
        name=payload.name,
    )
    return {"status": "ok", "reply": reply}


@router.get("/")
def list_messages(limit: int = 50, db: Session = Depends(get_db)):
    from ..models import MessageLog
    msgs = (
        db.query(MessageLog)
        .order_by(MessageLog.timestamp.desc())
        .limit(limit)
        .all()
    )
    return msgs
