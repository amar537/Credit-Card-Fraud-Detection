import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text, Float, Integer, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.database import Base


class PredictionFeedback(str, enum.Enum):
    CORRECT = "correct"
    INCORRECT = "incorrect"
    UNKNOWN = "unknown"


class Prediction(Base):
    __tablename__ = "predictions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("transactions.id"), nullable=False, unique=True, index=True)
    model_version = Column(String(50), nullable=False)
    fraud_probability = Column(Float, nullable=False)
    prediction_class = Column(Boolean, nullable=False)  # True if fraud, False if legitimate
    confidence_score = Column(Float, nullable=True)
    risk_level = Column(String(50), nullable=False, default="low")
    feature_importance = Column(JSONB)  # Store feature importance for explainability
    processing_time_ms = Column(Integer, nullable=False)
    feedback = Column(Enum(PredictionFeedback), default=PredictionFeedback.UNKNOWN)
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    feedback_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    transaction = relationship("Transaction", back_populates="prediction")
    reviewer = relationship("User", foreign_keys=[reviewed_by], back_populates="reviewed_predictions")
    
    def __repr__(self):
        return f"<Prediction(id={self.id}, fraud_probability={self.fraud_probability}, prediction={self.prediction_class})>"
