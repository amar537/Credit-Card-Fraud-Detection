"""
Machine Learning Module for Fraud Detection

This module contains:
- LSTM-RNN model implementation
- Feature engineering and preprocessing
- Model training and evaluation utilities
- Prediction service integration
"""

from .model import FraudDetectionLSTM
from .preprocessing import FeatureEngineer

__all__ = [
    "FraudDetectionLSTM",
    "FeatureEngineer"
]