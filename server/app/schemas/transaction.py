from typing import Optional, Dict, Any, Union
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, validator
import uuid
from pydantic import IPvAnyAddress

from app.models.transaction import TransactionType


class TransactionBase(BaseModel):
    amount: Decimal
    merchant_name: Optional[str] = None
    merchant_category: Optional[str] = None
    transaction_type: TransactionType
    location: Optional[str] = None
    ip_address: Optional[Union[str, IPvAnyAddress]] = None
    device_info: Optional[Dict[str, Any]] = None


class TransactionCreate(TransactionBase):
    card_id: uuid.UUID
    transaction_date: datetime
    
    @validator("amount")
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError("Amount must be greater than 0")
        if v > Decimal('99999999.99'):
            raise ValueError("Amount exceeds maximum limit")
        return v
    
    @validator("ip_address")
    def validate_ip_address(cls, v):
        if v is not None:
            # Basic IP validation
            parts = v.split('.')
            if len(parts) != 4:
                raise ValueError("Invalid IP address format")
            try:
                for part in parts:
                    num = int(part)
                    if num < 0 or num > 255:
                        raise ValueError("Invalid IP address")
            except ValueError:
                raise ValueError("Invalid IP address")
        return v


class TransactionUpdate(BaseModel):
    merchant_name: Optional[str] = None
    merchant_category: Optional[str] = None
    location: Optional[str] = None
    is_fraud: Optional[bool] = None
    fraud_score: Optional[float] = None


class TransactionResponse(TransactionBase):
    id: uuid.UUID
    card_id: uuid.UUID
    transaction_date: datetime
    is_fraud: Optional[bool] = None
    fraud_score: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TransactionStats(BaseModel):
    total_transactions: int
    total_amount: Decimal
    fraud_count: int
    fraud_rate: float
    avg_transaction_amount: Decimal
    max_transaction_amount: Decimal
    min_transaction_amount: Decimal


class TransactionFilters(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    merchant_name: Optional[str] = None
    merchant_category: Optional[str] = None
    transaction_type: Optional[TransactionType] = None
    is_fraud: Optional[bool] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    location: Optional[str] = None
    card_id: Optional[uuid.UUID] = None
    
    class Config:
        use_enum_values = True


class TransactionExport(BaseModel):
    format: str = "csv"  # csv, xlsx
    filters: Optional[TransactionFilters] = None


class TransactionListResponse(BaseModel):
    transactions: list[TransactionResponse]
    total: int
    page: int
    size: int
    has_more: bool


class BatchTransactionCreate(BaseModel):
    transactions: list[TransactionCreate]
    
    @validator("transactions")
    def validate_transactions(cls, v):
        if len(v) == 0:
            raise ValueError("At least one transaction is required")
        if len(v) > 1000:
            raise ValueError("Maximum 1000 transactions per batch")
        return v
