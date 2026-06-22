import enum
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Text, DateTime,
    Enum, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from .database import Base


class ContactRole(str, enum.Enum):
    farmer = "farmer"
    buyer = "buyer"
    trader = "trader"
    factory = "factory"
    unknown = "unknown"


class LotStatus(str, enum.Enum):
    draft = "draft"
    qualified = "qualified"
    ready_for_publication = "ready_for_publication"
    sent_to_yulia = "sent_to_yulia"
    archived = "archived"


class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=True)
    phone = Column(String, nullable=True, index=True)
    telegram_id = Column(String, nullable=True, index=True)
    whatsapp_id = Column(String, nullable=True, index=True)
    max_id = Column(String, nullable=True, index=True)
    region = Column(String, nullable=True)
    role = Column(Enum(ContactRole), default=ContactRole.unknown)
    crops = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    last_channel = Column(String, nullable=True)
    preferred_channel = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    lots = relationship("Lot", back_populates="contact")
    messages = relationship("MessageLog", back_populates="contact")


class Lot(Base):
    __tablename__ = "lots"

    id = Column(Integer, primary_key=True, index=True)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=False)
    culture = Column(String, nullable=True)
    volume = Column(Float, nullable=True)
    region = Column(String, nullable=True)
    district = Column(String, nullable=True)
    quality_type = Column(String, nullable=True)
    humidity = Column(Float, nullable=True)
    weed = Column(Float, nullable=True)
    grain_impurity = Column(Float, nullable=True)
    nature = Column(Float, nullable=True)
    oil_content = Column(Float, nullable=True)
    protein = Column(Float, nullable=True)
    acid_value = Column(Float, nullable=True)
    vat_type = Column(String, nullable=True)
    price = Column(Float, nullable=True)
    location = Column(String, nullable=True)
    documents = Column(String, nullable=True)
    analysis_photo = Column(String, nullable=True)
    status = Column(Enum(LotStatus), default=LotStatus.draft)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    contact = relationship("Contact", back_populates="lots")


class MessageLog(Base):
    __tablename__ = "message_logs"

    id = Column(Integer, primary_key=True, index=True)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=True)
    channel = Column(String, nullable=False)
    direction = Column(String, default="incoming")
    incoming_text = Column(Text, nullable=True)
    outgoing_text = Column(Text, nullable=True)
    extracted_data = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    contact = relationship("Contact", back_populates="messages")
