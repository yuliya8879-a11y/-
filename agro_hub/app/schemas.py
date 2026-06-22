from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import BaseModel
from .models import ContactRole, LotStatus


class ContactBase(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    telegram_id: Optional[str] = None
    whatsapp_id: Optional[str] = None
    max_id: Optional[str] = None
    region: Optional[str] = None
    role: Optional[ContactRole] = ContactRole.unknown
    crops: Optional[str] = None
    notes: Optional[str] = None
    last_channel: Optional[str] = None
    preferred_channel: Optional[str] = None


class ContactCreate(ContactBase):
    pass


class ContactUpdate(ContactBase):
    pass


class ContactOut(ContactBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LotBase(BaseModel):
    culture: Optional[str] = None
    volume: Optional[float] = None
    region: Optional[str] = None
    district: Optional[str] = None
    quality_type: Optional[str] = None
    humidity: Optional[float] = None
    weed: Optional[float] = None
    grain_impurity: Optional[float] = None
    nature: Optional[float] = None
    oil_content: Optional[float] = None
    protein: Optional[float] = None
    acid_value: Optional[float] = None
    vat_type: Optional[str] = None
    price: Optional[float] = None
    location: Optional[str] = None
    documents: Optional[str] = None
    analysis_photo: Optional[str] = None
    status: Optional[LotStatus] = LotStatus.draft


class LotCreate(LotBase):
    contact_id: int


class LotUpdate(LotBase):
    pass


class LotOut(LotBase):
    id: int
    contact_id: int
    created_at: datetime
    updated_at: datetime
    contact: Optional[ContactOut] = None

    class Config:
        from_attributes = True


class MessageLogBase(BaseModel):
    channel: str
    direction: str = "incoming"
    incoming_text: Optional[str] = None
    outgoing_text: Optional[str] = None
    extracted_data: Optional[Dict[str, Any]] = None


class MessageLogCreate(MessageLogBase):
    contact_id: Optional[int] = None


class MessageLogOut(MessageLogBase):
    id: int
    contact_id: Optional[int] = None
    timestamp: datetime

    class Config:
        from_attributes = True


class ManualMessageIn(BaseModel):
    channel: str
    sender_id: str
    phone: Optional[str] = None
    name: Optional[str] = None
    text: str


class DashboardStats(BaseModel):
    new_contacts_today: int
    total_contacts: int
    total_lots: int
    lots_draft: int
    lots_qualified: int
    lots_ready: int
    lots_sent_to_yulia: int
    lots_without_indicators: int


class DashboardResponse(BaseModel):
    stats: DashboardStats
    recent_lots: List[LotOut]
    pending_replies: List[ContactOut]
