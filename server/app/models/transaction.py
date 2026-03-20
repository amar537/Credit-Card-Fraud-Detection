import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, Boolean, ForeignKey, Enum, Text, DECIMAL, func
from sqlalchemy.dialects.postgresql import UUID, INET, JSONB
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum

from app.database import Base


class TransactionType(PyEnum):
    """Transaction type enumeration."""
    PURCHASE = "purchase"
    REFUND = "refund"
    CASH_ADVANCE = "cash_advance"
    PAYMENT = "payment"


class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    card_id = Column(UUID(as_uuid=True), ForeignKey("cards.id"), nullable=False, index=True)
    amount = Column(DECIMAL(10, 2), nullable=False)
    merchant_name = Column(String(255))
    merchant_category = Column(String(100))
    transaction_date = Column(DateTime(timezone=True), nullable=False, index=True)
    transaction_type = Column(Enum(TransactionType), nullable=False)
    location = Column(String(255))
    ip_address = Column(INET)
    device_info = Column(JSONB)
    is_fraud = Column(Boolean, nullable=True)  # Will be set by ML model
    fraud_score = Column(Float, nullable=True)  # Fraud probability from ML model
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    card = relationship("Card", back_populates="transactions")
    prediction = relationship("Prediction", back_populates="transaction", uselist=False, cascade="all, delete-orphan")
    fraud_alerts = relationship("FraudAlert", back_populates="transaction", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Transaction(id={self.id}, amount={self.amount}, merchant={self.merchant_name})>"
