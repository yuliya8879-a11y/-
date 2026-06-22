import logging
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from . import crud, models
from .ai_processor import extract_lot_data, determine_next_question
from .notifications import notify_yulia

logger = logging.getLogger(__name__)


async def handle_incoming_message(
    db: Session,
    channel: str,
    sender_id: str,
    text: str,
    phone: Optional[str] = None,
    name: Optional[str] = None,
) -> str:
    contact = crud.find_or_create_contact(db, channel, sender_id, phone, name)

    extracted = await extract_lot_data(text)
    logger.info(f"Извлечено из сообщения: {extracted}")

    lot = crud.get_active_draft_lot(db, contact.id)
    if lot is None:
        lot = crud.create_lot(db, contact.id)

    lot = crud.update_lot_from_extracted(db, lot, extracted)

    if contact.region and not lot.region:
        lot = crud.update_lot_from_extracted(db, lot, {"region": contact.region})

    crud.log_message(
        db, contact.id, channel, "incoming",
        incoming=text, outgoing=None, extracted=extracted
    )

    if lot.culture and lot.volume and lot.region and lot.status == models.LotStatus.draft:
        lot = crud.qualify_lot(db, lot)
        sent = await notify_yulia(lot, contact)
        if sent:
            lot = crud.mark_lot_sent_to_yulia(db, lot)
        logger.info(f"Лот {lot.id} квалифицирован, уведомление Юлии отправлено: {sent}")

    next_q = determine_next_question(lot)
    if next_q:
        reply = next_q
    else:
        reply = (
            "✅ Отлично! Все основные данные получены. "
            "Ваш лот передан менеджеру. Мы свяжемся с вами в ближайшее время."
        )

    crud.log_message(
        db, contact.id, channel, "outgoing",
        incoming=None, outgoing=reply
    )

    return reply
