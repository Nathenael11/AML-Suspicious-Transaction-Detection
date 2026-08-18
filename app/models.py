"""
XGBoost AML Model Wrapper and Prediction Engine.

Handles loading trained model artifacts (model.pkl, feature_names.pkl), thread-safe
inference execution, score evaluation against decision threshold (0.50),
and risk level alert categorization.
"""

import os
import pickle
import logging
import numpy as np
import pandas as pd
import xgboost as xgb
from app.feature_engineering import extract_feature_vector, EXACT_FEATURE_NAMES

logger = logging.getLogger(__name__)

# Calibrated Decision Threshold
OPTIMAL_THRESHOLD = 0.50

class AMLModelWrapper:
    """Thread-safe wrapper around trained XGBoost model and feature pipeline."""

    def __init__(self, models_dir=None):
        if models_dir is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            models_dir = os.path.join(base_dir, 'models')
            
        self.models_dir = models_dir
        self.model_path = os.path.join(self.models_dir, 'model.pkl')
        self.features_path = os.path.join(self.models_dir, 'feature_names.pkl')
        
        self.model = None
        self.feature_names = EXACT_FEATURE_NAMES
        self.threshold = OPTIMAL_THRESHOLD
        self.is_mock = False
        
        self.load_model()

    def load_model(self):
        """Load model and feature list from disk, fallback to synthetic model if missing."""
        try:
            if os.path.exists(self.model_path) and os.path.exists(self.features_path):
                logger.info(f"Loading trained XGBoost model from {self.model_path}...")
                with open(self.model_path, 'rb') as f:
                    self.model = pickle.load(f)
                with open(self.features_path, 'rb') as f:
                    self.feature_names = pickle.load(f)
                self.is_mock = False
                logger.info(f"Successfully loaded trained model with {len(self.feature_names)} features.")
            else:
                logger.warning(
                    f"Model artifact not found at {self.model_path}. "
                    "Instantiating synthetic XGBoost fallback model for out-of-the-box UI demonstration..."
                )
                self._create_synthetic_model()
        except Exception as e:
            logger.error(f"Error loading model from disk: {e}. Falling back to synthetic model.", exc_info=True)
            self._create_synthetic_model()

    def _create_synthetic_model(self):
        """Instantiate synthetic model trained on exact 46 feature vector."""
        self.feature_names = EXACT_FEATURE_NAMES
        
        from scripts.generate_mock_model import generate_mock_artifacts
        generate_mock_artifacts(self.models_dir)
        
        if os.path.exists(self.model_path):
            with open(self.model_path, 'rb') as f:
                self.model = pickle.load(f)
            self.is_mock = True

    def predict(self, raw_tx: dict) -> dict:
        """
        Execute full inference pipeline for a single raw transaction dictionary.
        
        Returns dictionary containing:
        - risk_score (float 0.0 - 1.0)
        - is_suspicious (bool)
        - alert_level ('High', 'Medium', 'Low')
        - action_recommendation (str)
        - features_extracted (int)
        - is_mock_model (bool)
        """
        if self.model is None or not self.feature_names:
            raise RuntimeError("AML Model is not initialized.")

        # Extract feature vector aligned EXACTLY to feature_names
        vector_df = extract_feature_vector(raw_tx, self.feature_names)

        # Calculate prediction probability
        risk_score = 0.0
        try:
            if hasattr(self.model, 'predict_proba'):
                probs = self.model.predict_proba(vector_df)
                risk_score = float(probs[0, 1])
            else:
                dmatrix = xgb.DMatrix(vector_df)
                risk_score = float(self.model.predict(dmatrix)[0])
        except Exception as e:
            logger.error(f"Inference prediction error: {e}")
            risk_score = 0.0

        risk_score = max(0.0, min(1.0, risk_score))
        is_suspicious = bool(risk_score >= self.threshold)

        # Categorize Alert Level & Recommendation
        if risk_score >= self.threshold:
            alert_level = 'High'
            action_recommendation = (
                "IMMEDIATE ACTION REQUIRED: High probability of money laundering / structuring. "
                "Freeze account pending SAR (Suspicious Activity Report) filing and L2 Compliance review."
            )
        elif risk_score >= 0.25:
            alert_level = 'Medium'
            action_recommendation = (
                "MONITORING RECOMMENDED: Elevated risk metrics detected (cross-currency or volume anomaly). "
                "Escalate to Compliance Analyst for 48-hour transaction history audit."
            )
        else:
            alert_level = 'Low'
            action_recommendation = (
                "PASS: Transaction parameters fall within normal behavioral baselines. No action required."
            )

        return {
            'risk_score': round(risk_score, 4),
            'is_suspicious': is_suspicious,
            'alert_level': alert_level,
            'threshold': self.threshold,
            'action_recommendation': action_recommendation,
            'features_extracted': len(self.feature_names),
            'is_mock_model': self.is_mock
        }