"""
Google Colab / Local Script: Train 9-Feature Simple Web Model for AML Shield.

This script trains a lightweight XGBoost model using ONLY the 9 raw web features
captured directly from HTML forms, bypassing complex graph feature requirements.

Instructions for Google Colab:
1. Copy and paste this complete script into a Google Colab cell.
2. Run the cell to generate 'model.pkl' and 'feature_names.pkl'.
3. Download the generated files and place them into your 'aml-webapp/models/' folder.
"""

import pickle
import numpy as np
import pandas as pd
import xgboost as xgb

# 9 Raw Web Form Features
WEB_FEATURE_NAMES = [
    'log_amount_paid',
    'log_amount_received',
    'amount_discrepancy',
    'currency_mismatch',
    'cross_bank',
    'self_loop',
    'hour_of_day',
    'day_of_week',
    'is_weekend'
]

def generate_simple_web_dataset(n_samples=2000):
    """Generate synthetic training dataset based on AML transaction patterns."""
    np.random.seed(42)
    
    data = []
    labels = []
    
    for i in range(n_samples):
        is_laundering = (i < int(n_samples * 0.2)) # 20% positive class
        
        if is_laundering:
            # Suspicious pattern: structuring ($9,999), self-loop, currency mismatch, 3 AM weekend
            amount_paid = np.random.choice([9999.99, 9990.00, 49500.00])
            amount_received = np.random.choice([9999.99, 41000.00])
            currency_mismatch = np.random.choice([0, 1], p=[0.2, 0.8])
            cross_bank = np.random.choice([0, 1], p=[0.7, 0.3])
            self_loop = np.random.choice([0, 1], p=[0.3, 0.7])
            hour_of_day = np.random.choice([1, 2, 3, 4, 23])
            day_of_week = np.random.choice([5, 6])
            labels.append(1)
        else:
            # Normal pattern: reasonable amounts, matching currency, standard business hours
            amount_paid = np.random.uniform(5.0, 1500.0)
            amount_received = amount_paid
            currency_mismatch = 0
            cross_bank = 1
            self_loop = 0
            hour_of_day = np.random.randint(8, 20)
            day_of_week = np.random.randint(0, 5)
            labels.append(0)

        log_amount_paid = np.log1p(amount_paid)
        log_amount_received = np.log1p(amount_received)
        amount_discrepancy = abs(amount_paid - amount_received)
        is_weekend = 1 if day_of_week >= 5 else 0

        data.append({
            'log_amount_paid': log_amount_paid,
            'log_amount_received': log_amount_received,
            'amount_discrepancy': amount_discrepancy,
            'currency_mismatch': currency_mismatch,
            'cross_bank': cross_bank,
            'self_loop': self_loop,
            'hour_of_day': hour_of_day,
            'day_of_week': day_of_week,
            'is_weekend': is_weekend
        })

    df = pd.DataFrame(data, columns=WEB_FEATURE_NAMES)
    y = np.array(labels)
    return df, y

def train_and_export_simple_model():
    """Train XGBoost model on 9 web features and save artifacts."""
    print("=== Training 9-Feature Simple Web XGBoost Model ===")
    X, y = generate_simple_web_dataset(n_samples=3000)
    
    model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.05,
        scale_pos_weight=3.0,
        random_state=42,
        eval_metric='aucpr'
    )
    
    model.fit(X, y)
    
    # Save model artifacts
    with open('model.pkl', 'wb') as f:
        pickle.dump(model, f)
        
    with open('feature_names.pkl', 'wb') as f:
        pickle.dump(WEB_FEATURE_NAMES, f)

    print("Success! Created 'model.pkl' and 'feature_names.pkl'.")
    print(f"Features (9): {WEB_FEATURE_NAMES}")

if __name__ == '__main__':
    train_and_export_simple_model()
