#!/usr/bin/env python3
"""
Complete training pipeline for fraud detection LSTM model.
Uses Kaggle Credit Card Fraud dataset.

Usage:
    python train_model.py --data-path data/creditcard.csv --output-dir ml_models/
"""

import os
import sys
import argparse
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Tuple, Dict, Any
import json
import pickle

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tensorflow as tf
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score, roc_curve
import matplotlib.pyplot as plt
import seaborn as sns

from app.ml.model import FraudDetectionModel
from app.ml.preprocessing import FeaturePreprocessor


class ModelTrainer:
    """Complete training pipeline for fraud detection."""
    
    def __init__(self, data_path: str, output_dir: str):
        self.data_path = data_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.model = FraudDetectionModel()
        self.preprocessor = FeaturePreprocessor()
        
        # Training parameters
        self.sequence_length = 10
        self.test_size = 0.2
        self.val_size = 0.1
        self.random_state = 42
        
    def load_and_preprocess_kaggle_data(self) -> pd.DataFrame:
        """Load and preprocess Kaggle Credit Card Fraud dataset."""
        print("Loading Kaggle Credit Card Fraud dataset...")
        
        # Load data
        df = pd.read_csv(self.data_path)
        print(f"Dataset shape: {df.shape}")
        print(f"Class distribution: {df['Class'].value_counts().to_dict()}")
        
        # Convert Time to datetime features
        df['datetime'] = pd.to_datetime(df['Time'], unit='s', origin='2013-09-01')
        df['hour'] = df['datetime'].dt.hour
        df['day'] = df['datetime'].dt.day
        df['month'] = df['datetime'].dt.month
        df['day_of_week'] = df['datetime'].dt.dayofweek
        df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
        
        # Add synthetic card_id (simulate multiple cards)
        np.random.seed(self.random_state)
        num_cards = 1000
        df['card_id'] = np.random.choice(range(1, num_cards + 1), size=len(df))
        
        # Add synthetic merchant categories
        merchant_categories = [
            'retail', 'restaurant', 'gas', 'grocery', 'entertainment',
            'travel', 'healthcare', 'education', 'utilities', 'online'
        ]
        df['merchant_category'] = np.random.choice(merchant_categories, size=len(df))
        
        # Add synthetic transaction types
        transaction_types = ['purchase', 'refund', 'cash_advance', 'payment']
        df['transaction_type'] = np.random.choice(transaction_types, size=len(df), p=[0.7, 0.1, 0.15, 0.05])
        
        # Add synthetic merchant names
        df['merchant_name'] = f"Merchant_{np.random.randint(1, 10000, size=len(df))}"
        
        # Rename columns to match our schema
        df = df.rename(columns={
            'V1': 'feature_v1',
            'V2': 'feature_v2',
            'Amount': 'amount',
            'Class': 'is_fraud'
        })
        
        # Add location and device info (synthetic)
        df['location'] = f"Location_{np.random.randint(1, 100, size=len(df))}"
        df['ip_address'] = f"192.168.{np.random.randint(1, 255)}.{np.random.randint(1, 255)}"
        df['device_info'] = json.dumps({
            'device_type': np.random.choice(['mobile', 'desktop', 'tablet']),
            'os': np.random.choice(['ios', 'android', 'windows', 'macos'])
        })
        
        # Select relevant columns for training
        feature_columns = [
            'amount', 'hour', 'day', 'month', 'day_of_week', 'is_weekend',
            'card_id', 'merchant_category', 'transaction_type', 'merchant_name',
            'location', 'ip_address', 'device_info', 'is_fraud'
        ]
        
        # Add V features if they exist
        v_features = [col for col in df.columns if col.startswith('feature_v')]
        feature_columns.extend(v_features)
        
        df = df[feature_columns].copy()
        
        # Convert datetime columns
        df['transaction_date'] = df['datetime']
        df = df.drop('datetime', axis=1)
        
        print(f"Preprocessed dataset shape: {df.shape}")
        print(f"Final class distribution: {df['is_fraud'].value_counts().to_dict()}")
        
        return df
    
    def prepare_training_data(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Prepare training, validation, and test datasets."""
        print("Preparing training data...")
        
        # Split data by card_id to avoid data leakage
        unique_cards = df['card_id'].unique()
        train_cards, temp_cards = train_test_split(
            unique_cards, test_size=(self.test_size + self.val_size), 
            random_state=self.random_state, stratify=None
        )
        
        val_cards, test_cards = train_test_split(
            temp_cards, test_size=self.test_size/(self.test_size + self.val_size),
            random_state=self.random_state
        )
        
        # Create splits
        train_df = df[df['card_id'].isin(train_cards)]
        val_df = df[df['card_id'].isin(val_cards)]
        test_df = df[df['card_id'].isin(test_cards)]
        
        print(f"Train: {len(train_df)} samples ({train_df['is_fraud'].mean():.3%} fraud)")
        print(f"Val: {len(val_df)} samples ({val_df['is_fraud'].mean():.3%} fraud)")
        print(f"Test: {len(test_df)} samples ({test_df['is_fraud'].mean():.3%} fraud)")
        
        # Feature engineering
        print("Performing feature engineering...")
        train_features = self.preprocessor.prepare_features(train_df, fit=True)
        val_features = self.preprocessor.prepare_features(val_df, fit=False)
        test_features = self.preprocessor.prepare_features(test_df, fit=False)
        
        # Create sequences
        print(f"Creating sequences (length={self.sequence_length})...")
        train_sequences = self.preprocessor.create_sequences(train_features, sequence_length=self.sequence_length)
        val_sequences = self.preprocessor.create_sequences(val_features, sequence_length=self.sequence_length)
        test_sequences = self.preprocessor.create_sequences(test_features, sequence_length=self.sequence_length)
        
        # Extract labels
        train_labels = train_df['is_fraud'].values[self.sequence_length-1:]
        val_labels = val_df['is_fraud'].values[self.sequence_length-1:]
        test_labels = test_df['is_fraud'].values[self.sequence_length-1:]
        
        print(f"Final shapes:")
        print(f"Train: {train_sequences.shape} -> {train_labels.shape}")
        print(f"Val: {val_sequences.shape} -> {val_labels.shape}")
        print(f"Test: {test_sequences.shape} -> {test_labels.shape}")
        
        return train_sequences, val_sequences, test_sequences, train_labels, val_labels, test_labels
    
    def train_model(
        self, 
        train_sequences: np.ndarray, 
        val_sequences: np.ndarray,
        train_labels: np.ndarray, 
        val_labels: np.ndarray
    ) -> Dict[str, Any]:
        """Train the LSTM model."""
        print("Training LSTM model...")
        
        # Calculate class weights for imbalanced data
        fraud_count = np.sum(train_labels == 1)
        normal_count = np.sum(train_labels == 0)
        class_weights = {
            0: 1.0,
            1: normal_count / fraud_count if fraud_count > 0 else 1.0
        }
        print(f"Class weights: {class_weights}")
        
        # Build model
        input_shape = (train_sequences.shape[1], train_sequences.shape[2])
        self.model.build_model(input_shape)
        
        # Setup callbacks
        callbacks = [
            tf.keras.callbacks.EarlyStopping(
                monitor='val_auc',
                patience=10,
                restore_best_weights=True,
                mode='max'
            ),
            tf.keras.callbacks.ModelCheckpoint(
                filepath=str(self.output_dir / 'best_model.h5'),
                monitor='val_auc',
                save_best_only=True,
                mode='max'
            ),
            tf.keras.callbacks.ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=5,
                min_lr=1e-7
            )
        ]
        
        # Train model
        history = self.model.train(
            train_sequences, train_labels,
            val_sequences, val_labels,
            epochs=50,
            batch_size=256,
            class_weights=class_weights,
            callbacks=callbacks
        )
        
        return history
    
    def evaluate_model(
        self, 
        test_sequences: np.ndarray, 
        test_labels: np.ndarray
    ) -> Dict[str, Any]:
        """Evaluate model on test set."""
        print("Evaluating model...")
        
        # Make predictions
        predictions_proba = self.model.predict(test_sequences)
        predictions = (predictions_proba > 0.5).astype(int).flatten()
        
        # Calculate metrics
        accuracy = np.mean(predictions == test_labels)
        precision = np.sum((predictions == 1) & (test_labels == 1)) / np.sum(predictions == 1) if np.sum(predictions == 1) > 0 else 0
        recall = np.sum((predictions == 1) & (test_labels == 1)) / np.sum(test_labels == 1) if np.sum(test_labels == 1) > 0 else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        auc_roc = roc_auc_score(test_labels, predictions_proba)
        
        # Classification report
        report = classification_report(test_labels, predictions, target_names=['Normal', 'Fraud'])
        
        # Confusion matrix
        cm = confusion_matrix(test_labels, predictions)
        
        # ROC curve
        fpr, tpr, _ = roc_curve(test_labels, predictions_proba)
        
        metrics = {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1_score,
            'auc_roc': auc_roc,
            'classification_report': report,
            'confusion_matrix': cm.tolist(),
            'roc_curve': {'fpr': fpr.tolist(), 'tpr': tpr.tolist()}
        }
        
        print(f"Test Results:")
        print(f"Accuracy: {accuracy:.4f}")
        print(f"Precision: {precision:.4f}")
        print(f"Recall: {recall:.4f}")
        print(f"F1-Score: {f1_score:.4f}")
        print(f"AUC-ROC: {auc_roc:.4f}")
        print("\nClassification Report:")
        print(report)
        
        return metrics
    
    def save_artifacts(self, metrics: Dict[str, Any], history: Dict[str, Any]):
        """Save model, scaler, and training artifacts."""
        print("Saving artifacts...")
        
        # Save model
        model_path = self.output_dir / 'lstm_fraud_model.h5'
        self.model.save_model(str(model_path))
        
        # Save preprocessor (scaler and encoders)
        preprocessor_path = self.output_dir / 'preprocessor.pkl'
        with open(preprocessor_path, 'wb') as f:
            pickle.dump(self.preprocessor, f)
        
        # Save training history
        history_path = self.output_dir / 'training_history.json'
        with open(history_path, 'w') as f:
            json.dump(history, f, indent=2)
        
        # Save metrics
        metrics_path = self.output_dir / 'metrics.json'
        with open(metrics_path, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        # Save model info
        model_info = {
            'model_type': 'LSTM-RNN',
            'sequence_length': self.sequence_length,
            'input_shape': list(self.model.model.input_shape) if hasattr(self.model.model, 'input_shape') else None,
            'total_params': self.model.model.count_params() if hasattr(self.model.model, 'count_params') else None,
            'training_date': datetime.now().isoformat(),
            'dataset_path': self.data_path,
            'metrics': {k: v for k, v in metrics.items() if isinstance(v, (int, float, str))}
        }
        
        info_path = self.output_dir / 'model_info.json'
        with open(info_path, 'w') as f:
            json.dump(model_info, f, indent=2)
        
        print(f"Artifacts saved to {self.output_dir}")
    
    def run_training(self):
        """Run complete training pipeline."""
        print("Starting fraud detection model training...")
        print(f"Data path: {self.data_path}")
        print(f"Output directory: {self.output_dir}")
        
        # Load and preprocess data
        df = self.load_and_preprocess_kaggle_data()
        
        # Prepare training data
        train_sequences, val_sequences, test_sequences, train_labels, val_labels, test_labels = \
            self.prepare_training_data(df)
        
        # Train model
        history = self.train_model(train_sequences, val_sequences, train_labels, val_labels)
        
        # Evaluate model
        metrics = self.evaluate_model(test_sequences, test_labels)
        
        # Save artifacts
        self.save_artifacts(metrics, history)
        
        print("Training completed successfully!")
        return metrics


def main():
    parser = argparse.ArgumentParser(description='Train fraud detection LSTM model')
    parser.add_argument('--data-path', required=True, help='Path to creditcard.csv dataset')
    parser.add_argument('--output-dir', default='ml_models', help='Output directory for model artifacts')
    parser.add_argument('--sequence-length', type=int, default=10, help='Sequence length for LSTM')
    
    args = parser.parse_args()
    
    # Validate data path
    if not os.path.exists(args.data_path):
        print(f"Error: Data file not found at {args.data_path}")
        print("Please download the Kaggle Credit Card Fraud dataset:")
        print("https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud")
        sys.exit(1)
    
    # Create trainer and run training
    trainer = ModelTrainer(args.data_path, args.output_dir)
    trainer.sequence_length = args.sequence_length
    
    try:
        metrics = trainer.run_training()
        print("\nTraining completed successfully!")
        print(f"Model saved to: {args.output_dir}")
        print(f"Test AUC-ROC: {metrics['auc_roc']:.4f}")
        
    except Exception as e:
        print(f"Training failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
