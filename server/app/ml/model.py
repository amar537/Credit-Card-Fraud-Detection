import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, models
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
import numpy as np
import joblib
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class FraudDetectionLSTM:
    """LSTM-RNN Model for Credit Card Fraud Detection"""
    
    def __init__(self, model_path: str = None):
        self.model = None
        self.scaler = None
        self.model_path = model_path
        
        if model_path and Path(model_path).exists():
            self.load_model(model_path)
    
    def build_model(self, input_shape: tuple) -> models.Model:
        """
        Build LSTM architecture
        
        Architecture:
        - Input: (sequence_length, num_features)
        - LSTM 1: 128 units, return_sequences=True
        - Dropout: 0.2
        - LSTM 2: 64 units
        - Dropout: 0.2
        - Dense 1: 32 units, ReLU
        - Dropout: 0.1
        - Output: 1 unit, Sigmoid
        """
        model = models.Sequential([
            # First LSTM layer
            layers.LSTM(
                128,
                return_sequences=True,
                input_shape=input_shape,
                name='lstm_1'
            ),
            layers.Dropout(0.2, name='dropout_1'),
            
            # Second LSTM layer
            layers.LSTM(64, return_sequences=False, name='lstm_2'),
            layers.Dropout(0.2, name='dropout_2'),
            
            # Dense layers
            layers.Dense(32, activation='relu', name='dense_1'),
            layers.Dropout(0.1, name='dropout_3'),
            
            # Output layer
            layers.Dense(1, activation='sigmoid', name='output')
        ])
        
        # Compile model
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.001),
            loss='binary_crossentropy',
            metrics=[
                'accuracy',
                keras.metrics.Precision(name='precision'),
                keras.metrics.Recall(name='recall'),
                keras.metrics.AUC(name='auc')
            ]
        )
        
        self.model = model
        return model
    
    def train(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray,
        y_val: np.ndarray,
        epochs: int = 50,
        batch_size: int = 256
    ):
        """Train the model with early stopping"""
        
        if self.model is None:
            self.build_model((X_train.shape[1], X_train.shape[2]))
        
        # Callbacks
        callbacks = [
            EarlyStopping(
                monitor='val_loss',
                patience=10,
                restore_best_weights=True,
                verbose=1
            ),
            ModelCheckpoint(
                'ml_models/lstm_best.h5',
                monitor='val_auc',
                save_best_only=True,
                mode='max',
                verbose=1
            ),
            ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=5,
                min_lr=0.00001,
                verbose=1
            )
        ]
        
        # Class weights for imbalanced data
        fraud_count = np.sum(y_train == 1)
        non_fraud_count = np.sum(y_train == 0)
        class_weight = {
            0: 1.0,
            1: non_fraud_count / fraud_count
        }
        
        # Train
        history = self.model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks,
            class_weight=class_weight,
            verbose=1
        )
        
        return history
    
    def predict(self, X: np.ndarray, threshold: float = 0.5) -> tuple:
        """
        Make predictions
        
        Returns:
            - predictions: Binary predictions (0 or 1)
            - probabilities: Fraud probabilities
        """
        if self.model is None:
            raise ValueError("Model not loaded. Call load_model() first.")
        
        probabilities = self.model.predict(X, verbose=0)
        predictions = (probabilities >= threshold).astype(int)
        
        return predictions.flatten(), probabilities.flatten()
    
    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray) -> dict:
        """Evaluate model performance"""
        results = self.model.evaluate(X_test, y_test, verbose=0)
        
        metrics = {
            'loss': results[0],
            'accuracy': results[1],
            'precision': results[2],
            'recall': results[3],
            'auc': results[4]
        }
        
        # Calculate F1-score
        metrics['f1_score'] = 2 * (metrics['precision'] * metrics['recall']) / \
                             (metrics['precision'] + metrics['recall'] + 1e-7)
        
        return metrics
    
    def save_model(self, path: str):
        """Save model and scaler"""
        self.model.save(path)
        if self.scaler:
            joblib.dump(self.scaler, path.replace('.h5', '_scaler.pkl'))
        logger.info(f"Model saved to {path}")
    
    def load_model(self, path: str):
        """Load model and scaler"""
        self.model = keras.models.load_model(path)
        scaler_path = path.replace('.h5', '_scaler.pkl')
        if Path(scaler_path).exists():
            self.scaler = joblib.load(scaler_path)
        logger.info(f"Model loaded from {path}")
