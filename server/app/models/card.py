import uuid
from datetime import datetime, date
from sqlalchemy import Column, String, Boolean, DateTime, Date, Text, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.database import Base


class CardType(str, enum.Enum):
    CREDIT = "credit"
    DEBIT = "debit"


class Card(Base):
    __tablename__ = "cards"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    card_number = Column(String(16), nullable=False)  # Encrypted in practice
    card_type = Column(Enum(CardType), nullable=False)
    card_brand = Column(String(50))  # Visa, Mastercard, etc.
    expiry_date = Column(Date, nullable=False)
    cvv = Column(String(3), nullable=False)  # Encrypted in practice
    billing_address = Column(Text)
    is_blocked = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="cards")
    transactions = relationship("Transaction", back_populates="card", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Card(id={self.id}, user_id={self.user_id}, card_type={self.card_type})>"
