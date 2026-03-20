import pytest
from datetime import datetime, timedelta
from app.models.transaction import Transaction
from app.models.card import Card


@pytest.fixture
def test_card(db, test_user):
    """Create a test card."""
    card = Card(
        user_id=test_user.id,
        card_number="4111111111111111",
        card_type="credit",
        expiry_month=12,
        expiry_year=2025,
        cvv="123",
        is_active=True
    )
    db.add(card)
    db.commit()
    db.refresh(card)
    return card


@pytest.fixture
def test_transaction(db, test_card):
    """Create a test transaction."""
    transaction = Transaction(
        card_id=test_card.id,
        amount=100.50,
        merchant_name="Test Merchant",
        merchant_category="retail",
        location="New York, NY",
        transaction_date=datetime.utcnow(),
        is_fraud=False,
        fraud_score=0.15
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction


def test_create_transaction(client, auth_headers, test_card):
    """Test creating a new transaction."""
    response = client.post(
        "/api/v1/transactions",
        headers=auth_headers,
        json={
            "card_id": str(test_card.id),
            "amount": "250.75",
            "merchant_name": "New Merchant",
            "merchant_category": "electronics",
            "location": "San Francisco, CA",
            "transaction_date": datetime.utcnow().isoformat()
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["amount"] == "250.75"
    assert data["merchant_name"] == "New Merchant"


def test_get_transactions(client, auth_headers, test_transaction):
    """Test getting list of transactions."""
    response = client.get("/api/v1/transactions", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "transactions" in data
    assert len(data["transactions"]) >= 1


def test_get_transaction_by_id(client, auth_headers, test_transaction):
    """Test getting a specific transaction."""
    response = client.get(
        f"/api/v1/transactions/{test_transaction.id}",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_transaction.id)
    assert data["amount"] == str(test_transaction.amount)


def test_get_transactions_with_filters(client, auth_headers, test_transaction):
    """Test getting transactions with filters."""
    # Filter by is_fraud
    response = client.get(
        "/api/v1/transactions?is_fraud=false",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "transactions" in data


def test_get_transactions_unauthorized(client):
    """Test getting transactions without authentication."""
    response = client.get("/api/v1/transactions")
    assert response.status_code == 401


def test_get_transaction_stats(client, auth_headers, test_transaction):
    """Test getting transaction statistics."""
    response = client.get("/api/v1/transactions/stats", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_transactions" in data
    assert "total_amount" in data
    assert "fraud_rate" in data

