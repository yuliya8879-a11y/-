from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import crud, schemas
from ..database import get_db
from ..models import Lot, LotStatus
from ..ai_processor import generate_ad_text

router = APIRouter(prefix="/api/lots", tags=["lots"])


@router.get("/", response_model=List[schemas.LotOut])
def list_lots(db: Session = Depends(get_db)):
    return crud.get_all_lots(db)


@router.get("/{lot_id}", response_model=schemas.LotOut)
def get_lot(lot_id: int, db: Session = Depends(get_db)):
    lot = db.query(Lot).filter(Lot.id == lot_id).first()
    if not lot:
        raise HTTPException(status_code=404, detail="Лот не найден")
    return lot


@router.patch("/{lot_id}", response_model=schemas.LotOut)
def update_lot(lot_id: int, data: schemas.LotUpdate, db: Session = Depends(get_db)):
    lot = db.query(Lot).filter(Lot.id == lot_id).first()
    if not lot:
        raise HTTPException(status_code=404, detail="Лот не найден")
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(lot, key, value)
    from datetime import datetime
    lot.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(lot)
    return lot


@router.post("/{lot_id}/archive", response_model=schemas.LotOut)
def archive_lot(lot_id: int, db: Session = Depends(get_db)):
    lot = db.query(Lot).filter(Lot.id == lot_id).first()
    if not lot:
        raise HTTPException(status_code=404, detail="Лот не найден")
    lot.status = LotStatus.archived
    from datetime import datetime
    lot.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(lot)
    return lot


@router.get("/{lot_id}/ad-text")
def get_ad_text(lot_id: int, db: Session = Depends(get_db)):
    lot = db.query(Lot).filter(Lot.id == lot_id).first()
    if not lot:
        raise HTTPException(status_code=404, detail="Лот не найден")
    text = generate_ad_text(lot, lot.contact)
    return {"ad_text": text}
