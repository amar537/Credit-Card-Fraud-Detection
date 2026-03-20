from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, validator


class PredictionRequest(BaseModel):
    transaction_id: str = Field(..., description="ID of the transaction to score")

    @validator("transaction_id")
    def validate_uuid(cls, value: str) -> str:
        if not value:
            raise ValueError("transaction_id is required")
        return value


class BatchPredictionRequest(BaseModel):
    transaction_ids: List[str]

    @validator("transaction_ids")
    def validate_transaction_ids(cls, values: List[str]) -> List[str]:
        if not values:
            raise ValueError("At least one transaction_id is required")
        if len(values) > 1000:
            raise ValueError("Batch size cannot exceed 1000")
        return values


class PredictionResponse(BaseModel):
    prediction_id: str
    transaction_id: str
    is_fraud: bool
    fraud_probability: float
    confidence_score: float
    risk_level: str
    model_version: str
    processing_time_ms: float
    timestamp: datetime
    fraud_alert_id: Optional[str] = None
    feature_importance: Optional[Dict[str, float]] = None


class BatchPredictionResponse(BaseModel):
    predictions: List[PredictionResponse]
    total_requested: int
    total_processed: int
    fraud_alerts_created: int
    fraud_alert_ids: List[str]


class PredictionHistory(BaseModel):
    predictions: List[PredictionResponse]
    total_count: int
    limit: int
    offset: int
    has_more: bool


class PredictionFeedbackRequest(BaseModel):
    is_correct_fraud: Optional[bool] = Field(
        None, description="Indicates whether the fraud prediction was accurate"
    )
    feedback_notes: Optional[str] = Field(
        None, description="Optional analyst feedback for model retraining"
    )


class PredictionStatisticsResponse(BaseModel):
    period_days: int
    total_predictions: int
    fraud_predictions: int
    fraud_rate: float
    high_risk_predictions: int
    high_risk_rate: float
    risk_level_breakdown: Dict[str, int]
    average_confidence: float
    start_date: datetime
    end_date: datetime
