"""
Create a dummy LSTM model for testing purposes
This allows the application to run without training a full model
"""

import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import joblib
from pathlib import Path
import json
import os

def create_dummy_lstm_model():
    """Create a simple LSTM model with random weights for testing"""
    
    # Model configuration (matching your actual architecture)
    sequence_length = 10
    num_features = 17  # Based on feature engineering pipeline
    
    print("🔨 Building dummy LSTM model...")
    
    model = keras.Sequential([
        layers.LSTM(128, return_sequences=True, input_shape=(sequence_length, num_features), name='lstm_1'),
        layers.Dropout(0.2, name='dropout_1'),
        layers.LSTM(64, return_sequences=False, name='lstm_2'),
        layers.Dropout(0.2, name='dropout_2'),
        layers.Dense(32, activation='relu', name='dense_1'),
        layers.Dropout(0.1, name='dropout_3'),
        layers.Dense(1, activation='sigmoid', name='output')
    ])
    
    # Compile
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=0.001),
        loss='binary_crossentropy',
        metrics=['accuracy', keras.metrics.Precision(), keras.metrics.Recall(), keras.metrics.AUC()]
    )
    
    print("✅ Model architecture created")
    print(model.summary())
    
    # Initialize weights with dummy data (simulates training)
    dummy_X = np.random.random((100, sequence_length, num_features))
    dummy_y = np.random.randint(0, 2, 100)
    
    print("\n🎯 Training with dummy data (1 epoch)...")
    model.fit(dummy_X, dummy_y, epochs=1, batch_size=32, verbose=1)
    
    # Save model
    model_path = Path("ml_models/lstm_fraud_model.h5")
    model_path.parent.mkdir(exist_ok=True)
    model.save(str(model_path))
    
    print(f"\n✅ Dummy model saved to: {model_path}")
    
    # Create dummy scaler
    try:
        from sklearn.preprocessing import StandardScaler
        scaler = StandardScaler()
        scaler.fit(np.random.random((100, num_features)))
        
        scaler_path = Path("ml_models/lstm_fraud_model_scaler.pkl")
        joblib.dump(scaler, str(scaler_path))
        
        print(f"✅ Dummy scaler saved to: {scaler_path}")
    except ImportError:
        print("⚠️  sklearn not available, creating dummy scaler")
        # Create a dummy scaler object
        dummy_scaler = {
            'mean': np.zeros(num_features),
            'scale': np.ones(num_features)
        }
        scaler_path = Path("ml_models/lstm_fraud_model_scaler.pkl")
        joblib.dump(dummy_scaler, str(scaler_path))
        print(f"✅ Dummy scaler saved to: {scaler_path}")
    
    # Create model metadata
    metadata = {
        "model_version": "v1.0-dummy",
        "created_at": "2024-01-01T00:00:00",
        "sequence_length": sequence_length,
        "num_features": num_features,
        "architecture": "LSTM-RNN",
        "status": "dummy_for_testing",
        "note": "This is a placeholder model. Train with real data for production use."
    }
    
    metadata_path = Path("ml_models/model_metadata.json")
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"✅ Metadata saved to: {metadata_path}")
    print("\n🎉 Dummy model creation complete!")
    print("\n⚠️  IMPORTANT: This is a TESTING model. Train with real data before production!")
    
    return model

if __name__ == "__main__":
    create_dummy_lstm_model()
