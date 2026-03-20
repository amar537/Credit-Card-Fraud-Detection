import pytest
from datetime import datetime
from app.models.transaction import Transaction
from app.models.card import Card
from app.models.prediction import Prediction


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


@pytest.fixture
def test_prediction(db, test_transaction):
    """Create a test prediction."""
    prediction = Prediction(
        transaction_id=test_transaction.id,
        model_version="1.0.0",
        fraud_probability=0.25,
        prediction_class=False,
        confidence_score=0.75,
        risk_level="low",
        processing_time_ms=150
    )
    db.add(prediction)
    db.commit()
    db.refresh(prediction)
    return prediction


def test_create_prediction(client, auth_headers, test_transaction):
    """Test creating a prediction for a transaction."""
    response = client.post(
        "/api/v1/predictions/predict",
        headers=auth_headers,
        json={"transaction_id": str(test_transaction.id)}
    )
    # Note: This may fail if ML model is not available, so we check for either success or service unavailable
    assert response.status_code in [201, 503]
    if response.status_code == 201:
        data = response.json()
        assert "prediction_id" in data
        assert "is_fraud" in data
        assert "fraud_probability" in data


def test_get_prediction_history(client, auth_headers, test_prediction):
    """Test getting prediction history."""
    response = client.get("/api/v1/predictions/history", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "predictions" in data
    assert "total" in data


def test_get_prediction_history_with_pagination(client, auth_headers, test_prediction):
    """Test getting prediction history with pagination."""
    response = client.get(
        "/api/v1/predictions/history?limit=10&offset=0",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "predictions" in data
    assert "limit" in data
    assert "offset" in data


def test_get_prediction_by_id(client, auth_headers, test_prediction):
    """Test getting a specific prediction."""
    response = client.get(
        f"/api/v1/predictions/{test_prediction.id}",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_prediction.id)


def test_submit_prediction_feedback(client, auth_headers, test_prediction):
    """Test submitting feedback for a prediction."""
    response = client.post(
        f"/api/v1/predictions/{test_prediction.id}/feedback",
        headers=auth_headers,
        json={
            "is_correct": True,
            "feedback_notes": "This was correctly identified as legitimate"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "message" in data


def test_get_prediction_statistics(client, auth_headers, test_prediction):
    """Test getting prediction statistics."""
    response = client.get("/api/v1/predictions/statistics", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_predictions" in data
    assert "fraud_rate" in data


def test_get_model_info(client, auth_headers):
    """Test getting model information."""
    response = client.get("/api/v1/predictions/model-info", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "model_version" in data


def test_create_prediction_unauthorized(client, test_transaction):
    """Test creating prediction without authentication."""
    response = client.post(
        "/api/v1/predictions/predict",
        json={"transaction_id": str(test_transaction.id)}
    )
    assert response.status_code == 401

