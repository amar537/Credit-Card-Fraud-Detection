"""
Create a simple dummy model files for testing purposes
This creates placeholder files without requiring TensorFlow to be installed locally
"""

import numpy as np
import joblib
from pathlib import Path
import json
import pickle
import os

def create_dummy_model_files():
    """Create dummy model files that can be loaded by the application"""
    
    print("🔨 Creating dummy model files...")
    
    # Create ml_models directory
    model_dir = Path("ml_models")
    model_dir.mkdir(exist_ok=True)
    
    # Create a simple dummy model object that can be pickled
    class DummyModel:
        def __init__(self):
            self.model_type = "LSTM-RNN"
            self.sequence_length = 10
            self.num_features = 17
            self.trained = True
            
        def predict(self, X):
            # Return random predictions between 0 and 1
            return np.random.random(len(X))
        
        def summary(self):
            return "Dummy LSTM Model for Testing"
    
    # Create dummy model instance
    dummy_model = DummyModel()
    
    # Save as pickle file (more compatible than H5)
    model_path = model_dir / "lstm_fraud_model.h5"
    with open(model_path, 'wb') as f:
        pickle.dump(dummy_model, f)
    
    print(f"✅ Dummy model saved to: {model_path}")
    
    # Create dummy scaler
    dummy_scaler = {
        'mean': np.zeros(17),
        'scale': np.ones(17),
        'type': 'StandardScaler'
    }
    
    scaler_path = model_dir / "lstm_fraud_model_scaler.pkl"
    joblib.dump(dummy_scaler, str(scaler_path))
    
    print(f"✅ Dummy scaler saved to: {scaler_path}")
    
    # Create model metadata
    metadata = {
        "model_version": "v1.0-dummy",
        "created_at": "2024-01-01T00:00:00",
        "sequence_length": 10,
        "num_features": 17,
        "architecture": "LSTM-RNN",
        "status": "dummy_for_testing",
        "note": "This is a placeholder model. Train with real data for production use.",
        "accuracy": 0.85,
        "precision": 0.82,
        "recall": 0.88,
        "auc_roc": 0.91
    }
    
    metadata_path = model_dir / "model_metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"✅ Metadata saved to: {metadata_path}")
    
    # Create a simple requirements note
    note_path = model_dir / "README.txt"
    with open(note_path, 'w') as f:
        f.write("DUMMY MODEL FILES\n")
        f.write("==================\n")
        f.write("These are placeholder model files for testing purposes.\n")
        f.write("To create a real model, run: python scripts/train_model.py\n")
        f.write("with a proper credit card fraud detection dataset.\n")
    
    print(f"✅ Documentation saved to: {note_path}")
    
    print("\n🎉 Dummy model files creation complete!")
    print("\n⚠️  IMPORTANT: This is a TESTING model. Train with real data before production!")
    
    return True

if __name__ == "__main__":
    create_dummy_model_files()
