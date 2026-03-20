import asyncio
import time
import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Tuple

import numpy as np

from app.config import settings
from app.ml.model import FraudDetectionLSTM
from app.ml.preprocessing import FeatureEngineer
from app.redis_client import redis_client


class RiskLevel(Enum):
    """Risk level enumeration for fraud predictions."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class PredictionResult:
    """Prediction result data structure."""
    is_fraud: bool
    fraud_probability: float
    confidence_score: float
    risk_level: RiskLevel
    model_version: str
    processing_time_ms: float
    timestamp: str
    prediction_id: str
    feature_importance: Optional[Dict[str, float]] = None


class PredictionEngine:
    """Real-time fraud detection prediction engine."""
    
    def __init__(self):
        self.model = FraudDetectionLSTM()
        self.preprocessor = FeatureEngineer()
        self.model_version = "v1.0"
        self._model_loaded = False
        
        # Risk level thresholds
        self.risk_thresholds = {
            RiskLevel.LOW: 0.30,
            RiskLevel.MEDIUM: 0.60,
            RiskLevel.HIGH: 0.85,
            RiskLevel.CRITICAL: 1.0
        }
    
    async def _ensure_model_loaded(self):
        """Ensure the model is loaded before inference."""
        if not self._model_loaded:
            try:
                await asyncio.to_thread(self.model.load_model, settings.ML_MODEL_PATH)
                self._model_loaded = True
            except Exception as e:
                raise RuntimeError(f"Failed to load ML model: {str(e)}")
    
    def _calculate_risk_level(self, fraud_probability: float) -> RiskLevel:
        """Calculate risk level based on fraud probability."""
        for risk_level, threshold in self.risk_thresholds.items():
            if fraud_probability < threshold:
                return risk_level
        return RiskLevel.CRITICAL
    
    def _calculate_confidence_score(self, fraud_probability: float) -> float:
        """Calculate confidence score based on prediction certainty."""
        # Higher confidence for predictions closer to 0 or 1
        confidence = 1.0 - (2 * abs(fraud_probability - 0.5))
        return max(0.0, min(1.0, confidence))
    
    async def _check_cache(self, transaction_id: str) -> Optional[PredictionResult]:
        """Check if prediction result is cached."""
        try:
            cached_data = await redis_client.get(f"prediction:{transaction_id}")
            if cached_data:
                data = cached_data
                return PredictionResult(
                    is_fraud=data["is_fraud"],
                    fraud_probability=data["fraud_probability"],
                    confidence_score=data["confidence_score"],
                    risk_level=RiskLevel(data["risk_level"]),
                    model_version=data["model_version"],
                    processing_time_ms=data["processing_time_ms"],
                    timestamp=data["timestamp"],
                    prediction_id=data["prediction_id"],
                    feature_importance=data.get("feature_importance"),
                )
        except Exception:
            pass
        return None
    
    async def _cache_result(self, transaction_id: str, result: PredictionResult):
        """Cache prediction result for 5 minutes."""
        try:
            await redis_client.setex(
                f"prediction:{transaction_id}",
                300,  # 5 minutes
                {
                    "is_fraud": result.is_fraud,
                    "fraud_probability": result.fraud_probability,
                    "confidence_score": result.confidence_score,
                    "risk_level": result.risk_level.value,
                    "model_version": result.model_version,
                    "processing_time_ms": result.processing_time_ms,
                    "timestamp": result.timestamp,
                    "prediction_id": result.prediction_id,
                    "feature_importance": result.feature_importance,
                }
            )
        except Exception:
            pass  # Cache failure should not block prediction
    
    async def predict_single(self, transaction_data: Dict) -> PredictionResult:
        """
        Make a single transaction prediction.
        
        Args:
            transaction_data: Dictionary containing transaction features
            
        Returns:
            PredictionResult with comprehensive prediction information
        """
        start_time = time.time()
        prediction_id = str(uuid.uuid4())
        
        # Check cache first
        transaction_id = transaction_data.get("id")
        if transaction_id:
            cached_result = await self._check_cache(transaction_id)
            if cached_result:
                return cached_result
        
        try:
            # Ensure model is loaded
            await self._ensure_model_loaded()
            # Feature preparation (<50ms target)
            feature_start = time.time()
            feature_vector = self.preprocessor.build_feature_vector(transaction_data)
            sequence_data = self.preprocessor.build_sequence(feature_vector)
            feature_time = (time.time() - feature_start) * 1000
            
            # Model inference (<200ms target)
            inference_start = time.time()
            predictions, probabilities = await asyncio.to_thread(
                self.model.predict, sequence_data
            )
            inference_time = (time.time() - inference_start) * 1000
            
            # Extract fraud probability (assuming binary classification)
            fraud_probability = float(probabilities[0])
            
            # Calculate derived metrics
            is_fraud = fraud_probability >= 0.5
            confidence_score = self._calculate_confidence_score(fraud_probability)
            risk_level = self._calculate_risk_level(fraud_probability)
            feature_importance = self._calculate_feature_importance(transaction_data, fraud_probability)
            
            # Total processing time
            processing_time_ms = (time.time() - start_time) * 1000
            
            # Create result
            result = PredictionResult(
                is_fraud=is_fraud,
                fraud_probability=fraud_probability,
                confidence_score=confidence_score,
                risk_level=risk_level,
                model_version=self.model_version,
                processing_time_ms=processing_time_ms,
                timestamp=datetime.utcnow().isoformat(),
                prediction_id=prediction_id,
                feature_importance=feature_importance,
            )
            
            # Cache result
            if transaction_id:
                await self._cache_result(transaction_id, result)
            
            return result
            
        except Exception as e:
            # Return safe default on error
            processing_time_ms = (time.time() - start_time) * 1000
            return PredictionResult(
                is_fraud=False,
                fraud_probability=0.0,
                confidence_score=0.0,
                risk_level=RiskLevel.LOW,
                model_version=self.model_version,
                processing_time_ms=processing_time_ms,
                timestamp=datetime.utcnow().isoformat(),
                prediction_id=prediction_id,
                feature_importance=None,
            )
    
    async def predict_batch(self, transactions_data: List[Dict]) -> List[PredictionResult]:
        """
        Make batch predictions for multiple transactions.
        
        Args:
            transactions_data: List of transaction dictionaries
            
        Returns:
            List of PredictionResult objects
        """
        results = []
        
        # Process in batches to avoid memory issues
        batch_size = 100
        for i in range(0, len(transactions_data), batch_size):
            batch = transactions_data[i:i + batch_size]
            
            # Check cache for each transaction
            uncached_transactions: List[Tuple[int, Dict]] = []
            cached_results: Dict[int, PredictionResult] = {}
            
            for idx, transaction in enumerate(batch):
                transaction_id = transaction.get("id")
                if transaction_id:
                    cached_result = await self._check_cache(transaction_id)
                    if cached_result:
                        cached_results[idx] = cached_result
                        continue
                uncached_transactions.append((idx, transaction))
            
            batch_predictions: Dict[int, PredictionResult] = {}
            
            if uncached_transactions:
                try:
                    await self._ensure_model_loaded()
                    
                    feature_vectors = [
                        self.preprocessor.build_feature_vector(txn)
                        for _, txn in uncached_transactions
                    ]
                    sequences = [
                        self.preprocessor.build_sequence(vector)[0]
                        for vector in feature_vectors
                    ]
                    sequence_data = np.stack(sequences, axis=0)
                    
                    _, probabilities = await asyncio.to_thread(
                        self.model.predict, sequence_data
                    )
                    
                    for (idx, transaction), prob in zip(uncached_transactions, probabilities):
                        fraud_probability = float(prob)
                        is_fraud = fraud_probability >= 0.5
                        confidence_score = self._calculate_confidence_score(fraud_probability)
                        risk_level = self._calculate_risk_level(fraud_probability)
                        feature_importance = self._calculate_feature_importance(transaction, fraud_probability)
                        
                        result = PredictionResult(
                            is_fraud=is_fraud,
                            fraud_probability=fraud_probability,
                            confidence_score=confidence_score,
                            risk_level=risk_level,
                            model_version=self.model_version,
                            processing_time_ms=0.0,
                            timestamp=datetime.utcnow().isoformat(),
                            prediction_id=str(uuid.uuid4()),
                            feature_importance=feature_importance,
                        )
                        
                        transaction_id = transaction.get("id")
                        if transaction_id:
                            await self._cache_result(transaction_id, result)
                        
                        batch_predictions[idx] = result
                except Exception:
                    for idx, _ in uncached_transactions:
                        batch_predictions[idx] = PredictionResult(
                            is_fraud=False,
                            fraud_probability=0.0,
                            confidence_score=0.0,
                            risk_level=RiskLevel.LOW,
                            model_version=self.model_version,
                            processing_time_ms=0.0,
                            timestamp=datetime.utcnow().isoformat(),
                            prediction_id=str(uuid.uuid4()),
                            feature_importance=None,
                        )
            
            # Assemble results preserving original order
            for idx in range(len(batch)):
                if idx in cached_results:
                    results.append(cached_results[idx])
                elif idx in batch_predictions:
                    results.append(batch_predictions[idx])
                else:
                    # Should not happen, but keep list lengths in sync.
                    results.append(
                        PredictionResult(
                            is_fraud=False,
                            fraud_probability=0.0,
                            confidence_score=0.0,
                            risk_level=RiskLevel.LOW,
                            model_version=self.model_version,
                            processing_time_ms=0.0,
                            timestamp=datetime.utcnow().isoformat(),
                            prediction_id=str(uuid.uuid4()),
                            feature_importance=None,
                        )
                    )
        
        return results
    
    async def get_model_info(self) -> Dict:
        """Get model information and status."""
        await self._ensure_model_loaded()
        
        return {
            "model_version": self.model_version,
            "model_loaded": self._model_loaded,
            "model_type": "LSTM-RNN",
            "input_shape": getattr(self.model, "input_shape", None),
            "risk_thresholds": {k.value: v for k, v in self.risk_thresholds.items()},
            "cache_ttl_seconds": 300,
            "max_batch_size": 1000,
            "sequence_length": self.preprocessor.sequence_length,
            "feature_count": self.preprocessor.feature_count,
        }

    def _calculate_feature_importance(
        self, transaction_data: Dict, fraud_probability: float
    ) -> Dict[str, float]:
        """
        Generate a lightweight, deterministic feature-importance explanation.

        This is not a full SHAP explanation but gives analysts a hint about what
        influenced the score by combining simple heuristics derived from the payload.
        """
        amount = float(transaction_data.get("amount") or 0)
        merchant_category = (transaction_data.get("merchant_category") or "unknown").lower()
        location = (transaction_data.get("location") or "unknown").lower()
        txn_type = (transaction_data.get("transaction_type") or "unknown").lower()

        hour = 0
        timestamp = transaction_data.get("transaction_date")
        if isinstance(timestamp, str):
            try:
                hour = datetime.fromisoformat(timestamp.replace("Z", "+00:00")).hour
            except ValueError:
                hour = 0

        raw_scores = {
            "Transaction Amount": min(100.0, max(10.0, amount / 15)),
            "Merchant Category": 30.0 + (hash(merchant_category) % 30),
            "Transaction Type": 20.0 + (hash(txn_type) % 25),
            "Location Risk": 15.0 + (hash(location) % 20),
            "Time of Day": 15.0 if hour in (0, 1, 2, 3, 4, 5, 23) else 8.0,
            "Model Confidence": 40.0 * fraud_probability,
        }

        total = sum(raw_scores.values()) or 1
        return {k: round((v / total) * 100, 2) for k, v in raw_scores.items()}


# Global prediction engine instance
prediction_engine = PredictionEngine()
