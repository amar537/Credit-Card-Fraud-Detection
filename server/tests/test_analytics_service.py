import asyncio
from datetime import datetime, timedelta, date
import types
import pytest

from app.services.analytics_service import analytics_service
from app import redis_client as redis_module


class MockResult:
    def __init__(self, scalar_value=None, first_value=None, scalars_list=None, rows=None):
        self._scalar = scalar_value
        self._first = first_value
        self._scalars = scalars_list or []
        self._rows = rows or []

    def scalar(self):
        return self._scalar

    def first(self):
        return self._first

    def scalars(self):
        class _S:
            def __init__(self, data):
                self._data = data
            def all(self):
                return list(self._data)
        return _S(self._scalars)

    def all(self):
        return list(self._rows)


class MockAsyncSession:
    def __init__(self, results):
        self._results = list(results)
    async def execute(self, *_args, **_kwargs):
        return self._results.pop(0)


@pytest.mark.asyncio
async def test_get_dashboard_metrics_no_cache(monkeypatch):
    # Monkeypatch redis to disable cache
    async def fake_get(_):
        return None
    async def fake_set(*_args, **_kwargs):
        return True
    monkeypatch.setattr(redis_module.redis_client, "get", fake_get, raising=True)
    monkeypatch.setattr(redis_module.redis_client, "set", fake_set, raising=True)

    # Prepare DB execute call sequence: total, sum amount, fraud count, avg amount,
    # high risk alerts, active cards, predictions aggregates
    results = [
        MockResult(scalar_value=4),                # total_transactions
        MockResult(scalar_value=2050.88),          # total_amount
        MockResult(scalar_value=2),                # fraud_count
        MockResult(scalar_value=512.72),           # avg_amount
        MockResult(scalar_value=1),                # high_risk_alerts
        MockResult(scalar_value=2),                # active_cards
        MockResult(first_value=(0.9, 37.0, 2)),    # predictions aggregates
    ]
    db = MockAsyncSession(results)

    user_id = __import__("uuid").uuid4()
    metrics = await analytics_service.get_dashboard_metrics(db, user_id, days=7)

    assert metrics["total_transactions"] == 4
    assert float(metrics["total_amount"]) == 2050.88
    assert metrics["fraud_count"] == 2
    assert metrics["high_risk_alerts"] == 1
    assert metrics["active_cards"] == 2
    assert metrics["total_transactions"] > 0


@pytest.mark.asyncio
async def test_get_fraud_trends(monkeypatch):
    # disable cache
    async def fake_get(_):
        return None
    async def fake_set(*_args, **_kwargs):
        return True
    monkeypatch.setattr(redis_module.redis_client, "get", fake_get, raising=True)
    monkeypatch.setattr(redis_module.redis_client, "set", fake_set, raising=True)

    class Row:
        def __init__(self, d, total, fraud, total_amt, fraud_amt):
            self.period_date = d
            self.total_transactions = total
            self.fraud_transactions = fraud
            self.total_amount = total_amt
            self.fraud_amount = fraud_amt

    today = datetime.utcnow().date()
    rows = [
        Row(datetime.utcnow() - timedelta(days=1), 2, 1, 100.0, 50.0),
        Row(datetime.utcnow(), 3, 0, 200.0, 0.0),
    ]

    db = MockAsyncSession([MockResult(rows=rows)])
    user_id = __import__("uuid").uuid4()

    resp = await analytics_service.get_fraud_trends(db, user_id, days=7, period="daily")
    assert resp["period"] == "daily"
    assert len(resp["trends"]) == 2
    assert resp["summary"]["total_transactions"] == 5
