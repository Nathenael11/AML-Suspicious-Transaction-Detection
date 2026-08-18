"""
Generate Mock XGBoost Model and Feature Names Artifacts (46 Exact Features).

Builds a valid XGBoost Classifier trained on synthetic data matching the exact 46 features
from the AML training notebook. Evaluates Scenario A (Normal) as LOW risk and Scenario B (Suspicious) as HIGH risk.
"""

import os
import sys
import pickle
import numpy as np
import pandas as pd
import xgboost as xgb

# Ensure root directory is on sys.path
script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(script_dir, '..'))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from app.feature_engineering import EXACT_FEATURE_NAMES, transform_transaction, extract_feature_vector

def generate_mock_artifacts(models_dir):
    """Generate model.pkl and feature_names.pkl with exact 46 feature names."""
    os.makedirs(models_dir, exist_ok=True)
    
    model_path = os.path.join(models_dir, 'model.pkl')
    features_path = os.path.join(models_dir, 'feature_names.pkl')
    
    np.random.seed(42)
    n_samples = 1500
    n_features = len(EXACT_FEATURE_NAMES)
    
    # Build synthetic feature matrix
    X = np.zeros((n_samples, n_features))
    y = np.zeros(n_samples)

    for i in range(n_samples):
        # 30% suspicious samples, 70% normal samples
        is_susp = (i < int(0.3 * n_samples))
        
        if is_susp:
            tx = {
                'amount_paid': np.random.choice([9999.99, 9500.0, 48000.0]),
                'amount_received': np.random.choice([9999.99, 41000.0]),
                'payment_currency': 'US Dollar',
                'receiving_currency': np.random.choice(['Euro', 'JPY']),
                'from_bank': '010',
                'to_bank': '010',
                'from_account': '8000EBD30',
                'to_account': '8000EBD30',
                'payment_format': np.random.choice(['Reinvestment', 'Wire Transfer']),
                'hour_of_day': 3,
                'day_of_week': 6
            }
            y[i] = 1
        else:
            tx = {
                'amount_paid': np.random.uniform(10.0, 500.0),
                'amount_received': np.random.uniform(10.0, 500.0),
                'payment_currency': 'US Dollar',
                'receiving_currency': 'US Dollar',
                'from_bank': '001',
                'to_bank': '002',
                'from_account': '8000F4580',
                'to_account': '8000F5340',
                'payment_format': np.random.choice(['Credit Card', 'ACH']),
                'hour_of_day': np.random.randint(8, 20),
                'day_of_week': np.random.randint(0, 5)
            }
            y[i] = 0

        vec = extract_feature_vector(tx, EXACT_FEATURE_NAMES)
        X[i, :] = vec.values[0]

    model = xgb.XGBClassifier(
        n_estimators=60,
        max_depth=5,
        learning_rate=0.08,
        scale_pos_weight=2.5,
        random_state=42,
        eval_metric='aucpr'
    )
    
    model.fit(X, y)
    
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
        
    with open(features_path, 'wb') as f:
        pickle.dump(EXACT_FEATURE_NAMES, f)
        
    print(f"Successfully saved mock model ({len(EXACT_FEATURE_NAMES)} features) to {model_path}")
    print(f"Successfully saved feature names to {features_path}")

if __name__ == '__main__':
    script_dir = os.path.dirname(os.path.abspath(__file__))
    target_models_dir = os.path.abspath(os.path.join(script_dir, '..', 'models'))
    generate_mock_artifacts(target_models_dir)
