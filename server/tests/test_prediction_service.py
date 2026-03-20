import pytest
from datetime import datetime
from uuid import uuid4

from app.services.prediction_service import prediction_service


class MockResult:
    def __init__(self, scalar_value=None, scalars_list=None):
        self._scalar = scalar_value
        self._scalars = scalars_list or []

    def scalar(self):
        return self._scalar

    def scalars(self):
        class _S:
            def __init__(self, data):
                self._data = data
            def all(self):
                return list(self._data)
        return _S(self._scalars)


class MockPrediction:
    def __init__(self, id):
        self.id = id
        self.transaction_id = uuid4()
        self.prediction_class = True
        self.fraud_probability = 0.9
        self.confidence_score = 0.88
        self.risk_level = "low"
        self.model_version = "v1"
        self.processing_time_ms = 35
        self.created_at = datetime.utcnow()
        self.feature_importance = {"amount": 0.5}


class MockAsyncSession:
    def __init__(self, results):
        self._results = list(results)
    async def execute(self, *_args, **_kwargs):
        return self._results.pop(0)


@pytest.mark.asyncio
async def test_get_prediction_history_basic():
    # First call: count, second: list of scalars (predictions)
    preds = [MockPrediction(uuid4()), MockPrediction(uuid4())]
    db = MockAsyncSession([
        MockResult(scalar_value=len(preds)),
        MockResult(scalars_list=preds),
    ])

    user_id = uuid4()
    items, total = await prediction_service.get_prediction_history(
        db=db,
        user_id=user_id,
        limit=10,
        offset=0,
        start_date=None,
        end_date=None,
        risk_level=None,
    )

    assert total == 2
    assert len(items) == 2
    assert items[0].fraud_probability == 0.9
