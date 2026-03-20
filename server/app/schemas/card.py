from typing import Optional
from datetime import date, datetime
from pydantic import BaseModel, validator
import uuid

from app.models.card import CardType


class CardBase(BaseModel):
    card_number: str
    card_type: CardType
    card_brand: Optional[str] = None
    expiry_date: date
    cvv: str
    billing_address: Optional[str] = None


class CardCreate(CardBase):
    @validator("card_number")
    def validate_card_number(cls, v):
        # Remove spaces and dashes
        cleaned = v.replace(" ", "").replace("-", "")
        if len(cleaned) != 16:
            raise ValueError("Card number must be 16 digits")
        if not cleaned.isdigit():
            raise ValueError("Card number must contain only digits")
        
        # Luhn algorithm validation
        total = 0
        for i, digit in enumerate(reversed(cleaned)):
            n = int(digit)
            if i % 2 == 1:
                n *= 2
                if n > 9:
                    n -= 9
            total += n
        
        if total % 10 != 0:
            raise ValueError("Invalid card number (failed Luhn check)")
        
        return cleaned
    
    @validator("cvv")
    def validate_cvv(cls, v):
        if len(v) != 3 or not v.isdigit():
            raise ValueError("CVV must be 3 digits")
        return v
    
    @validator("expiry_date")
    def validate_expiry_date(cls, v):
        if v <= date.today():
            raise ValueError("Card has expired or expires today")
        return v


class CardUpdate(BaseModel):
    card_brand: Optional[str] = None
    billing_address: Optional[str] = None
    is_blocked: Optional[bool] = None


class CardResponse(CardBase):
    id: uuid.UUID
    user_id: uuid.UUID
    is_blocked: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    # Don't expose sensitive data in responses
    card_number: str  # Masked version
    cvv: str  # Masked version
    
    class Config:
        from_attributes = True
    
    @validator("card_number", pre=True)
    def mask_card_number(cls, v):
        if isinstance(v, str) and len(v) == 16:
            return f"****-****-****-{v[-4:]}"
        return v
    
    @validator("cvv", pre=True)
    def mask_cvv(cls, v):
        return "***"


class CardBlock(BaseModel):
    reason: Optional[str] = None


class CardUnblock(BaseModel):
    reason: Optional[str] = None
