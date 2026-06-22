from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import or_
from . import models, schemas


def get_contact_by_channel_id(db: Session, channel: str, channel_id: str) -> Optional[models.Contact]:
    if channel == "telegram":
        return db.query(models.Contact).filter(models.Contact.telegram_id == channel_id).first()
    elif channel == "whatsapp":
        return db.query(models.Contact).filter(
            or_(models.Contact.whatsapp_id == channel_id, models.Contact.phone == channel_id)
        ).first()
    elif channel == "max":
        return db.query(models.Contact).filter(models.Contact.max_id == channel_id).first()
    return None


def get_contact_by_phone(db: Session, phone: str) -> Optional[models.Contact]:
    return db.query(models.Contact).filter(models.Contact.phone == phone).first()


def find_or_create_contact(
    db: Session, channel: str, channel_id: str,
    phone: Optional[str] = None, name: Optional[str] = None
) -> models.Contact:
    contact = get_contact_by_channel_id(db, channel, channel_id)

    if not contact and phone:
        contact = get_contact_by_phone(db, phone)

    if contact:
        changed = False
        if channel == "telegram" and not contact.telegram_id:
            contact.telegram_id = channel_id
            changed = True
        elif channel == "whatsapp" and not contact.whatsapp_id:
            contact.whatsapp_id = channel_id
            changed = True
        elif channel == "max" and not contact.max_id:
            contact.max_id = channel_id
            changed = True
        if phone and not contact.phone:
            contact.phone = phone
            changed = True
        if name and not contact.name:
            contact.name = name
            changed = True
        contact.last_channel = channel
        contact.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(contact)
        return contact

    data = {"last_channel": channel, "preferred_channel": channel}
    if channel == "telegram":
        data["telegram_id"] = channel_id
    elif channel == "whatsapp":
        data["whatsapp_id"] = channel_id
        if phone:
            data["phone"] = phone
    elif channel == "max":
        data["max_id"] = channel_id
    if phone:
        data["phone"] = phone
    if name:
        data["name"] = name

    contact = models.Contact(**data)
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


def get_active_draft_lot(db: Session, contact_id: int) -> Optional[models.Lot]:
    return db.query(models.Lot).filter(
        models.Lot.contact_id == contact_id,
        models.Lot.status == models.LotStatus.draft
    ).order_by(models.Lot.created_at.desc()).first()


def create_lot(db: Session, contact_id: int) -> models.Lot:
    lot = models.Lot(contact_id=contact_id, status=models.LotStatus.draft)
    db.add(lot)
    db.commit()
    db.refresh(lot)
    return lot


def update_lot_from_extracted(db: Session, lot: models.Lot, data: dict) -> models.Lot:
    fields = [
        "culture", "volume", "region", "district", "quality_type",
        "humidity", "weed", "grain_impurity", "nature", "oil_content",
        "protein", "acid_value", "vat_type", "price"
    ]
    changed = False
    for field in fields:
        value = data.get(field)
        if value is not None and getattr(lot, field) is None:
            setattr(lot, field, value)
            changed = True
    if changed:
        lot.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(lot)
    return lot


def qualify_lot(db: Session, lot: models.Lot) -> models.Lot:
    lot.status = models.LotStatus.qualified
    lot.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(lot)
    return lot


def mark_lot_sent_to_yulia(db: Session, lot: models.Lot) -> models.Lot:
    lot.status = models.LotStatus.sent_to_yulia
    lot.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(lot)
    return lot


def log_message(
    db: Session, contact_id: Optional[int], channel: str,
    direction: str, incoming: Optional[str], outgoing: Optional[str],
    extracted: Optional[dict] = None
) -> models.MessageLog:
    msg = models.MessageLog(
        contact_id=contact_id,
        channel=channel,
        direction=direction,
        incoming_text=incoming,
        outgoing_text=outgoing,
        extracted_data=extracted,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


def get_dashboard_stats(db: Session) -> dict:
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    new_contacts_today = db.query(models.Contact).filter(
        models.Contact.created_at >= today
    ).count()
    total_contacts = db.query(models.Contact).count()
    total_lots = db.query(models.Lot).count()
    lots_draft = db.query(models.Lot).filter(models.Lot.status == models.LotStatus.draft).count()
    lots_qualified = db.query(models.Lot).filter(models.Lot.status == models.LotStatus.qualified).count()
    lots_ready = db.query(models.Lot).filter(
        models.Lot.status == models.LotStatus.ready_for_publication
    ).count()
    lots_sent = db.query(models.Lot).filter(models.Lot.status == models.LotStatus.sent_to_yulia).count()
    lots_without = db.query(models.Lot).filter(
        models.Lot.culture.isnot(None),
        models.Lot.humidity.is_(None),
        models.Lot.status != models.LotStatus.archived
    ).count()

    return {
        "new_contacts_today": new_contacts_today,
        "total_contacts": total_contacts,
        "total_lots": total_lots,
        "lots_draft": lots_draft,
        "lots_qualified": lots_qualified,
        "lots_ready": lots_ready,
        "lots_sent_to_yulia": lots_sent,
        "lots_without_indicators": lots_without,
    }


def get_recent_lots(db: Session, limit: int = 10) -> List[models.Lot]:
    return (
        db.query(models.Lot)
        .filter(models.Lot.status != models.LotStatus.archived)
        .order_by(models.Lot.created_at.desc())
        .limit(limit)
        .all()
    )


def get_pending_reply_contacts(db: Session) -> List[models.Contact]:
    since = datetime.utcnow() - timedelta(hours=24)
    contact_ids = (
        db.query(models.MessageLog.contact_id)
        .filter(
            models.MessageLog.direction == "incoming",
            models.MessageLog.timestamp >= since,
            models.MessageLog.contact_id.isnot(None),
        )
        .distinct()
        .subquery()
    )
    return db.query(models.Contact).filter(models.Contact.id.in_(contact_ids)).all()


def get_all_lots(db: Session) -> List[models.Lot]:
    return db.query(models.Lot).order_by(models.Lot.created_at.desc()).all()


def get_all_contacts(db: Session) -> List[models.Contact]:
    return db.query(models.Contact).order_by(models.Contact.created_at.desc()).all()


def update_contact(db: Session, contact: models.Contact, data: dict) -> models.Contact:
    for key, value in data.items():
        if hasattr(contact, key) and value is not None:
            setattr(contact, key, value)
    contact.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(contact)
    return contact
