#!/usr/bin/env python3
"""Seed the database with an initial admin user, cards, and transactions."""

from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from sqlalchemy.orm import Session

# Ensure we can import the app package when executing as a script
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from app.database import SessionLocal  # noqa: E402
from app.models.user import User  # noqa: E402
from app.models.card import Card, CardType  # noqa: E402
from app.models.transaction import (  # noqa: E402
    Transaction,
    TransactionType,
)
from app.models.prediction import Prediction, PredictionFeedback  # noqa: E402
from app.models.fraud_alert import FraudAlert, AlertLevel  # noqa: E402
from app.core.security import get_password_hash  # noqa: E402

ADMIN_EMAIL = "admin@fraudwatch.ai"
ADMIN_USERNAME = "admin"


def get_or_create_admin(session: Session) -> User:
    user = session.query(User).filter(User.email == ADMIN_EMAIL).one_or_none()
    if user:
        return user

    user = User(
        email=ADMIN_EMAIL,
        username=ADMIN_USERNAME,
        hashed_password=get_password_hash("ChangeMe123!"),
        full_name="FraudWatch Admin",
        is_active=True,
        is_superuser=True,
        is_verified=True,
    )
    session.add(user)
    session.flush()
    return user


def create_sample_cards(session: Session, user: User) -> list[Card]:
    cards = session.query(Card).filter(Card.user_id == user.id).all()
    if cards:
        return cards

    sample_cards = [
        Card(
            user_id=user.id,
            card_number="4111111111111111",
            card_type=CardType.CREDIT,
            card_brand="Visa",
            expiry_date=datetime.utcnow().date().replace(year=datetime.utcnow().year + 3),
            cvv="123",
            billing_address="123 Fraud St, Secure City, SC 90210",
        ),
        Card(
            user_id=user.id,
            card_number="5500000000000004",
            card_type=CardType.DEBIT,
            card_brand="Mastercard",
            expiry_date=datetime.utcnow().date().replace(year=datetime.utcnow().year + 2),
            cvv="456",
            billing_address="456 Trust Ave, Safe Town, ST 10001",
        ),
    ]
    session.add_all(sample_cards)
    session.flush()
    return sample_cards


def create_sample_transactions(session: Session, card: Card) -> list[Transaction]:
    existing = session.query(Transaction).filter(Transaction.card_id == card.id).limit(3).all()
    if existing:
        return existing

    now = datetime.utcnow()
    txns = [
        Transaction(
            card_id=card.id,
            amount=Decimal("125.45"),
            merchant_name="Retail_0421",
            merchant_category="retail",
            transaction_date=now - timedelta(days=2),
            transaction_type=TransactionType.PURCHASE,
            location="City_5",
            ip_address="192.168.5.10",
            device_info={"device_type": "mobile", "os": "ios"},
            is_fraud=False,
            fraud_score=0.12,
        ),
        Transaction(
            card_id=card.id,
            amount=Decimal("899.99"),
            merchant_name="Electronics_0784",
            merchant_category="electronics",
            transaction_date=now - timedelta(days=1, hours=3),
            transaction_type=TransactionType.PURCHASE,
            location="City_14",
            ip_address="10.0.14.77",
            device_info={"device_type": "desktop", "os": "windows"},
            is_fraud=True,
            fraud_score=0.91,
        ),
    ]
    session.add_all(txns)
    session.flush()
    return txns


def attach_prediction_and_alert(session: Session, transaction: Transaction) -> None:
    if not transaction.is_fraud:
        return

    prediction = session.query(Prediction).filter(Prediction.transaction_id == transaction.id).one_or_none()
    if not prediction:
        prediction = Prediction(
            transaction_id=transaction.id,
            model_version="v1.0.0",
            fraud_probability=transaction.fraud_score or 0.5,
            prediction_class=True,
            confidence_score=0.88,
            feature_importance={"amount": 0.45, "merchant_category": 0.22},
            processing_time_ms=37,
            feedback=PredictionFeedback.UNKNOWN,
        )
        session.add(prediction)

    alert = session.query(FraudAlert).filter(FraudAlert.transaction_id == transaction.id).one_or_none()
    if not alert:
        alert = FraudAlert(
            transaction_id=transaction.id,
            alert_level=AlertLevel.HIGH,
            alert_message="Large electronics purchase flagged as high risk.",
            is_resolved=False,
        )
        session.add(alert)


def seed() -> None:
    session = SessionLocal()
    try:
        admin = get_or_create_admin(session)
        cards = create_sample_cards(session, admin)
        for card in cards:
            transactions = create_sample_transactions(session, card)
            for txn in transactions:
                attach_prediction_and_alert(session, txn)
        session.commit()
        print("✅ Database seed completed. Admin credentials: admin@fraudwatch.ai / ChangeMe123!")
    except Exception as exc:  # pragma: no cover
        session.rollback()
        print(f"❌ Seed failed: {exc}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed()
