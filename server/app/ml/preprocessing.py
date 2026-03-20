"""Utilities to convert domain objects into model-ready feature tensors."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import joblib
import numpy as np

from app.config import settings


def _safe_float(value: Optional[float]) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _safe_int(value: Optional[int]) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


@dataclass
class FeatureEngineer:
    """
    Lightweight feature builder for inference-time transactions.

    The training pipeline historically relied on pandas-heavy rolling windows,
    but the real-time API only has the current transaction available. This
    class focuses on deterministic single-transaction features that map to the
    expected 17 inputs of the deployed LSTM model and optionally applies the
    persisted StandardScaler when available.
    """

    sequence_length: int = 10
    feature_count: int = 17
    merchant_map: Dict[str, int] = field(default_factory=dict)
    transaction_type_map: Dict[str, int] = field(default_factory=dict)
    device_type_map: Dict[str, int] = field(default_factory=dict)

    def __post_init__(self):
        self._scaler = None
        scaler_path = Path(settings.ML_SCALER_PATH)
        if scaler_path.exists():
            try:
                self._scaler = joblib.load(scaler_path)
            except Exception:
                self._scaler = None

    # --------------------------------------------------------------------- #
    # Public API
    # --------------------------------------------------------------------- #
    def build_feature_vector(self, transaction: Dict) -> np.ndarray:
        """Return a 1D feature vector for a transaction."""
        dt = self._parse_timestamp(transaction.get("transaction_date"))
        amount = _safe_float(transaction.get("amount"))

        merchant_category = (transaction.get("merchant_category") or "unknown").lower()
        transaction_type = (transaction.get("transaction_type") or "unknown").lower()
        device_type = self._extract_device_type(transaction.get("device_info"))

        vector = np.array(
            [
                amount,
                np.log1p(amount),
                dt.hour if dt else 0,
                dt.day if dt else 0,
                dt.month if dt else 0,
                dt.weekday() if dt else 0,
                1.0 if dt and dt.weekday() >= 5 else 0.0,
                self._encode_value(self.merchant_map, merchant_category),
                self._encode_value(self.transaction_type_map, transaction_type),
                self._encode_value(self.device_type_map, device_type),
                self._location_risk_score(transaction.get("location")),
                self._ip_risk_score(transaction.get("ip_address")),
                self._card_risk_score(transaction.get("card_id")),
                self._velocity_proxy(amount, transaction.get("card_id")),
                self._merchant_velocity_proxy(transaction.get("merchant_name")),
                self._amount_percentile_hint(amount),
                self._recent_activity_hint(dt),
            ],
            dtype=np.float32,
        )

        if self._scaler is not None:
            try:
                vector = self._scaler.transform(vector.reshape(1, -1))[0]
            except Exception:
                # Fall back to unscaled vector if the saved scaler is incompatible.
                pass

        return vector

    def build_sequence(
        self,
        feature_vector: np.ndarray,
        history_vectors: Optional[List[np.ndarray]] = None,
    ) -> np.ndarray:
        """
        Construct an LSTM input tensor of shape (1, sequence_length, feature_count).

        When no history is provided we repeat the current vector so the model still
        receives the expected time steps.
        """
        if feature_vector.shape[0] != self.feature_count:
            raise ValueError(
                f"Expected {self.feature_count} features, got {feature_vector.shape[0]}"
            )

        if history_vectors:
            stacked = np.vstack(history_vectors + [feature_vector])
            stacked = stacked[-self.sequence_length :]
        else:
            stacked = np.repeat(feature_vector[np.newaxis, :], self.sequence_length, axis=0)

        if stacked.shape[0] < self.sequence_length:
            padding = np.repeat(stacked[0:1], self.sequence_length - stacked.shape[0], axis=0)
            stacked = np.vstack([padding, stacked])

        return stacked.astype(np.float32)[np.newaxis, :, :]

    def prepare_batch_sequences(self, transactions: List[Dict]) -> np.ndarray:
        """Convenience helper used by the batch prediction endpoint."""
        sequences = [self.build_sequence(self.build_feature_vector(txn)) for txn in transactions]
        if not sequences:
            return np.zeros((0, self.sequence_length, self.feature_count), dtype=np.float32)
        return np.vstack(sequences)

    # --------------------------------------------------------------------- #
    # Helpers
    # --------------------------------------------------------------------- #
    def _parse_timestamp(self, value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None

    def _encode_value(self, mapping: Dict[str, int], raw_value: str) -> float:
        key = raw_value.strip().lower() if raw_value else "unknown"
        if key not in mapping:
            mapping[key] = len(mapping) + 1
        return float(mapping[key])

    def _extract_device_type(self, device_info: Optional[str]) -> str:
        if not device_info:
            return "unknown"
        try:
            if isinstance(device_info, str):
                info = json.loads(device_info)
            else:
                info = device_info
        except json.JSONDecodeError:
            return "unknown"
        return (info.get("device_type") or info.get("type") or "unknown").lower()

    def _location_risk_score(self, location: Optional[str]) -> float:
        if not location:
            return 0.0
        return float((hash(location.lower()) % 100) / 100)

    def _ip_risk_score(self, ip_address: Optional[str]) -> float:
        if not ip_address:
            return 0.0
        try:
            octets = [int(part) for part in ip_address.split(".")]
            return float(sum(octets) % 100) / 100
        except ValueError:
            return 0.0

    def _card_risk_score(self, card_id: Optional[str]) -> float:
        if not card_id:
            return 0.0
        return float((hash(card_id) % 100) / 100)

    def _velocity_proxy(self, amount: float, card_id: Optional[str]) -> float:
        base = amount / 1000.0
        if card_id:
            base += ((hash(card_id) % 5) / 10.0)
        return float(min(base, 1.0))

    def _merchant_velocity_proxy(self, merchant_name: Optional[str]) -> float:
        if not merchant_name:
            return 0.0
        return float((hash(merchant_name.lower()) % 100) / 100)

    def _amount_percentile_hint(self, amount: float) -> float:
        # Simple heuristic percentile using a sigmoid-like curve.
        return float(1.0 / (1.0 + np.exp(-amount / 500)))

    def _recent_activity_hint(self, dt: Optional[datetime]) -> float:
        if not dt:
            return 0.0
        # Higher score for night-time transactions.
        return float(1.0 if dt.hour < 6 or dt.hour > 22 else 0.0)
