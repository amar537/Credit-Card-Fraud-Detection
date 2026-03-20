#!/usr/bin/env python3
"""
Generate synthetic transaction data for testing the fraud detection system.

Usage:
    python generate_test_data.py --output data/synthetic_transactions.csv --samples 10000
"""

import os
import sys
import argparse
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import json
import uuid

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class SyntheticDataGenerator:
    """Generate realistic synthetic transaction data for testing."""
    
    def __init__(self, num_samples: int = 10000, fraud_ratio: float = 0.05):
        self.num_samples = num_samples
        self.fraud_ratio = fraud_ratio
        self.num_fraud = int(num_samples * fraud_ratio)
        self.num_normal = num_samples - self.num_fraud
        
        # Set random seed for reproducibility
        np.random.seed(42)
        
        # Data parameters
        self.card_ids = [str(uuid.uuid4()) for _ in range(1000)]  # 1000 unique cards
        self.merchant_categories = [
            'retail', 'restaurant', 'gas', 'grocery', 'entertainment',
            'travel', 'healthcare', 'education', 'utilities', 'online',
            'electronics', 'clothing', 'home_improvement', 'sports', 'pharmacy'
        ]
        self.transaction_types = ['purchase', 'refund', 'cash_advance', 'payment']
        self.locations = [f"City_{i}" for i in range(50)]
        
        # Amount distributions (USD)
        self.normal_amount_mean = 85.0
        self.normal_amount_std = 45.0
        self.fraud_amount_mean = 250.0
        self.fraud_amount_std = 180.0
        
    def generate_normal_transactions(self) -> pd.DataFrame:
        """Generate normal (non-fraudulent) transactions."""
        print(f"Generating {self.num_normal} normal transactions...")
        
        transactions = []
        start_date = datetime.now() - timedelta(days=90)
        
        for i in range(self.num_normal):
            # Generate realistic datetime (more transactions during business hours)
            hour = np.random.choice(
                np.arange(24), 
                p=[0.02, 0.01, 0.01, 0.01, 0.02, 0.03, 0.05, 0.08, 0.09, 0.08, 0.07, 0.06,
                   0.07, 0.06, 0.06, 0.06, 0.07, 0.08, 0.09, 0.08, 0.07, 0.05, 0.03, 0.02]
            )
            
            # Random date within last 90 days
            days_ago = np.random.exponential(scale=30)  # More recent transactions
            days_ago = min(days_ago, 90)
            transaction_date = start_date + timedelta(days=days_ago, hours=hour, 
                                                     minutes=np.random.randint(0, 60))
            
            # Generate amount (log-normal distribution for realistic amounts)
            amount = np.random.lognormal(
                mean=np.log(self.normal_amount_mean), 
                sigma=self.normal_amount_std / self.normal_amount_mean
            )
            amount = max(0.01, min(amount, 1000))  # Clamp between $0.01 and $1000
            
            # Select card (some cards have more transactions)
            card_weights = np.random.exponential(scale=1.0, size=len(self.card_ids))
            card_weights = card_weights / card_weights.sum()
            card_id = np.random.choice(self.card_ids, p=card_weights)
            
            # Merchant category (weighted by typical spending patterns)
            category_probs = {
                'retail': 0.25, 'restaurant': 0.15, 'gas': 0.12, 'grocery': 0.18,
                'entertainment': 0.08, 'travel': 0.05, 'healthcare': 0.04, 'education': 0.02,
                'utilities': 0.03, 'online': 0.08
            }
            merchant_category = np.random.choice(
                self.merchant_categories, 
                p=[category_probs.get(cat, 0.01) for cat in self.merchant_categories]
            )
            
            # Transaction type (mostly purchases)
            transaction_type = np.random.choice(
                self.transaction_types, 
                p=[0.85, 0.08, 0.04, 0.03]
            )
            
            # Generate merchant name
            merchant_name = f"{merchant_category.title()}_{np.random.randint(1, 1000):04d}"
            
            # Location (same as merchant category city)
            location = np.random.choice(self.locations)
            
            # IP address (geographically consistent with location)
            ip_address = f"192.168.{hash(location) % 255 + 1}.{np.random.randint(1, 255)}"
            
            # Device info
            device_types = ['mobile', 'desktop', 'tablet']
            device_type = np.random.choice(device_types, p=[0.6, 0.3, 0.1])
            os_choices = {
                'mobile': ['ios', 'android'],
                'desktop': ['windows', 'macos', 'linux'],
                'tablet': ['ios', 'android']
            }
            device_info = json.dumps({
                'device_type': device_type,
                'os': np.random.choice(os_choices[device_type])
            })
            
            transactions.append({
                'id': str(uuid.uuid4()),
                'card_id': card_id,
                'amount': round(amount, 2),
                'merchant_name': merchant_name,
                'merchant_category': merchant_category,
                'transaction_date': transaction_date.isoformat(),
                'transaction_type': transaction_type,
                'location': location,
                'ip_address': ip_address,
                'device_info': device_info,
                'is_fraud': False,
                'fraud_score': np.random.uniform(0.0, 0.3),  # Low fraud scores for normal transactions
                'created_at': transaction_date.isoformat(),
                'updated_at': transaction_date.isoformat()
            })
        
        return pd.DataFrame(transactions)
    
    def generate_fraudulent_transactions(self) -> pd.DataFrame:
        """Generate fraudulent transactions with realistic patterns."""
        print(f"Generating {self.num_fraud} fraudulent transactions...")
        
        transactions = []
        start_date = datetime.now() - timedelta(days=90)
        
        for i in range(self.num_fraud):
            # Fraudulent transactions often occur at unusual hours
            hour = np.random.choice(
                np.arange(24), 
                p=[0.05, 0.06, 0.07, 0.08, 0.06, 0.04, 0.03, 0.02, 0.02, 0.02, 0.02, 0.02,
                   0.02, 0.02, 0.02, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.07, 0.06]
            )
            
            # More recent transactions (fraud is often time-sensitive)
            days_ago = np.random.exponential(scale=7)  # More concentrated in recent days
            days_ago = min(days_ago, 90)
            transaction_date = start_date + timedelta(days=days_ago, hours=hour, 
                                                     minutes=np.random.randint(0, 60))
            
            # Higher amounts for fraud
            amount = np.random.lognormal(
                mean=np.log(self.fraud_amount_mean), 
                sigma=self.fraud_amount_std / self.fraud_amount_mean
            )
            amount = max(10.0, min(amount, 2000))  # Clamp between $10 and $2000
            
            # Random card (fraud can target any card)
            card_id = np.random.choice(self.card_ids)
            
            # Fraud patterns in merchant categories
            fraud_categories = ['online', 'electronics', 'clothing', 'travel', 'entertainment']
            if np.random.random() < 0.7:  # 70% chance of high-risk category
                merchant_category = np.random.choice(fraud_categories)
            else:
                merchant_category = np.random.choice(self.merchant_categories)
            
            # Transaction type (mostly purchases for fraud)
            transaction_type = np.random.choice(
                self.transaction_types, 
                p=[0.95, 0.02, 0.02, 0.01]
            )
            
            # Generate merchant name
            merchant_name = f"{merchant_category.title()}_{np.random.randint(1, 500):04d}"
            
            # Location (often different from card's usual locations)
            location = np.random.choice(self.locations)
            
            # IP address (often suspicious - different geolocation)
            ip_address = f"10.0.{np.random.randint(1, 255)}.{np.random.randint(1, 255)}"
            
            # Device info (often suspicious or unusual)
            if np.random.random() < 0.4:  # 40% chance of suspicious device
                device_info = json.dumps({
                    'device_type': 'unknown',
                    'os': 'unknown',
                    'user_agent': 'suspicious_bot'
                })
            else:
                device_type = np.random.choice(['mobile', 'desktop'], p=[0.7, 0.3])
                device_info = json.dumps({
                    'device_type': device_type,
                    'os': np.random.choice(['ios', 'android', 'windows'])
                })
            
            # High fraud scores
            fraud_score = np.random.uniform(0.6, 0.98)
            
            transactions.append({
                'id': str(uuid.uuid4()),
                'card_id': card_id,
                'amount': round(amount, 2),
                'merchant_name': merchant_name,
                'merchant_category': merchant_category,
                'transaction_date': transaction_date.isoformat(),
                'transaction_type': transaction_type,
                'location': location,
                'ip_address': ip_address,
                'device_info': device_info,
                'is_fraud': True,
                'fraud_score': fraud_score,
                'created_at': transaction_date.isoformat(),
                'updated_at': transaction_date.isoformat()
            })
        
        return pd.DataFrame(transactions)
    
    def generate_data(self) -> pd.DataFrame:
        """Generate complete synthetic dataset."""
        print(f"Generating {self.num_samples} synthetic transactions...")
        print(f"Fraud ratio: {self.fraud_ratio:.2%}")
        
        # Generate normal and fraudulent transactions
        normal_df = self.generate_normal_transactions()
        fraud_df = self.generate_fraudulent_transactions()
        
        # Combine and shuffle
        combined_df = pd.concat([normal_df, fraud_df], ignore_index=True)
        combined_df = combined_df.sample(frac=1, random_state=42).reset_index(drop=True)
        
        # Sort by transaction date for realistic sequence
        combined_df['transaction_date'] = pd.to_datetime(combined_df['transaction_date'])
        combined_df = combined_df.sort_values('transaction_date').reset_index(drop=True)
        
        # Convert dates back to string format
        combined_df['transaction_date'] = combined_df['transaction_date'].dt.isoformat()
        
        print(f"Generated dataset shape: {combined_df.shape}")
        print(f"Actual fraud ratio: {combined_df['is_fraud'].mean():.2%}")
        print(f"Date range: {combined_df['transaction_date'].min()} to {combined_df['transaction_date'].max()}")
        
        return combined_df
    
    def save_data(self, df: pd.DataFrame, output_path: str):
        """Save generated data to CSV file."""
        print(f"Saving data to {output_path}...")
        
        # Create output directory if it doesn't exist
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save to CSV
        df.to_csv(output_path, index=False)
        
        # Generate summary statistics
        summary = {
            'total_samples': len(df),
            'fraud_samples': df['is_fraud'].sum(),
            'normal_samples': len(df) - df['is_fraud'].sum(),
            'fraud_ratio': df['is_fraud'].mean(),
            'date_range': {
                'start': df['transaction_date'].min(),
                'end': df['transaction_date'].max()
            },
            'amount_stats': {
                'mean': df['amount'].mean(),
                'std': df['amount'].std(),
                'min': df['amount'].min(),
                'max': df['amount'].max()
            },
            'unique_cards': df['card_id'].nunique(),
            'unique_merchants': df['merchant_name'].nunique(),
            'merchant_categories': df['merchant_category'].value_counts().to_dict(),
            'transaction_types': df['transaction_type'].value_counts().to_dict()
        }
        
        # Save summary
        summary_path = output_path.replace('.csv', '_summary.json')
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"Data saved successfully!")
        print(f"Summary statistics saved to: {summary_path}")
        
        return summary


def main():
    parser = argparse.ArgumentParser(description='Generate synthetic transaction data for testing')
    parser.add_argument('--output', default='data/synthetic_transactions.csv', 
                       help='Output CSV file path')
    parser.add_argument('--samples', type=int, default=10000, 
                       help='Number of samples to generate')
    parser.add_argument('--fraud-ratio', type=float, default=0.05, 
                       help='Ratio of fraudulent transactions (0.0-1.0)')
    
    args = parser.parse_args()
    
    # Validate parameters
    if args.samples <= 0:
        print("Error: Number of samples must be positive")
        sys.exit(1)
    
    if not 0 <= args.fraud_ratio <= 1:
        print("Error: Fraud ratio must be between 0.0 and 1.0")
        sys.exit(1)
    
    # Generate data
    generator = SyntheticDataGenerator(args.samples, args.fraud_ratio)
    
    try:
        df = generator.generate_data()
        summary = generator.save_data(df, args.output)
        
        print("\nData generation completed successfully!")
        print(f"Output file: {args.output}")
        print(f"Total samples: {summary['total_samples']}")
        print(f"Fraud samples: {summary['fraud_samples']}")
        print(f"Fraud ratio: {summary['fraud_ratio']:.2%}")
        
    except Exception as e:
        print(f"Data generation failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
