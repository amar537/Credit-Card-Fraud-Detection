from typing import Optional, Dict, Any, List
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel


class DashboardMetrics(BaseModel):
    total_transactions: int
    total_amount: Decimal
    fraud_count: int
    fraud_rate: float
    avg_transaction_amount: Decimal
    high_risk_alerts: int
    active_cards: int
    active_users: int
    model_accuracy: float
    avg_prediction_time_ms: float
    date_range_start: date
    date_range_end: date


class FraudTrend(BaseModel):
    date: date
    total_transactions: int
    fraud_transactions: int
    fraud_rate: float
    total_amount: Decimal
    fraud_amount: Decimal


class FraudTrendsResponse(BaseModel):
    trends: List[FraudTrend]
    period: str  # daily, weekly, monthly
    start_date: date
    end_date: date
    summary: Dict[str, Any]


class FraudPattern(BaseModel):
    pattern_type: str
    description: str
    frequency: int
    risk_level: str
    examples: List[Dict[str, Any]]
    mitigation_suggestions: List[str]


class FraudPatternsResponse(BaseModel):
    patterns: List[FraudPattern]
    total_patterns: int
    analysis_date: datetime


class GeographicFraudData(BaseModel):
    location: str
    transaction_count: int
    fraud_count: int
    fraud_rate: float
    total_amount: Decimal
    risk_score: float


class GeographicAnalysis(BaseModel):
    data: List[GeographicFraudData]
    total_locations: int
    high_risk_locations: List[str]
    analysis_date: datetime


class MerchantCategoryAnalysis(BaseModel):
    category: str
    transaction_count: int
    fraud_count: int
    fraud_rate: float
    avg_amount: Decimal
    risk_score: float


class TimeSeriesData(BaseModel):
    timestamp: datetime
    value: float
    label: str


class TimeSeriesAnalysis(BaseModel):
    data: List[TimeSeriesData]
    metric: str  # fraud_rate, transaction_volume, avg_amount
    period: str
    trend_direction: str  # increasing, decreasing, stable
    trend_strength: float


class AnalyticsFilters(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    merchant_categories: Optional[List[str]] = None
    locations: Optional[List[str]] = None
    card_types: Optional[List[str]] = None
    transaction_types: Optional[List[str]] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None


class AlertSummary(BaseModel):
    total_alerts: int
    critical_alerts: int
    high_alerts: int
    medium_alerts: int
    low_alerts: int
    resolved_alerts: int
    pending_alerts: int
    avg_resolution_time_hours: float


class ModelMetrics(BaseModel):
    model_version: str
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    auc_roc: float
    confusion_matrix: Dict[str, int]
    feature_importance: Dict[str, float]
    training_data_size: int
    last_updated: datetime


class PerformanceMetrics(BaseModel):
    api_response_time_ms: Dict[str, float]
    database_query_time_ms: Dict[str, float]
    model_inference_time_ms: float
    cache_hit_rate: float
    error_rate: float
    uptime_percentage: float
    memory_usage_mb: float
    cpu_usage_percentage: float
