from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import crud, schemas
from ..database import get_db

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/")
def get_dashboard(db: Session = Depends(get_db)):
    stats = crud.get_dashboard_stats(db)
    recent_lots = crud.get_recent_lots(db, limit=10)
    pending = crud.get_pending_reply_contacts(db)

    lots_data = []
    for lot in recent_lots:
        lot_dict = {
            "id": lot.id,
            "culture": lot.culture,
            "volume": lot.volume,
            "region": lot.region,
            "quality_type": lot.quality_type,
            "status": lot.status.value if lot.status else None,
            "created_at": lot.created_at.isoformat() if lot.created_at else None,
            "contact": {
                "id": lot.contact.id,
                "name": lot.contact.name,
                "phone": lot.contact.phone,
                "last_channel": lot.contact.last_channel,
            } if lot.contact else None,
        }
        lots_data.append(lot_dict)

    pending_data = [
        {
            "id": c.id,
            "name": c.name,
            "phone": c.phone,
            "last_channel": c.last_channel,
        }
        for c in pending
    ]

    return {
        "stats": stats,
        "recent_lots": lots_data,
        "pending_replies": pending_data,
    }
