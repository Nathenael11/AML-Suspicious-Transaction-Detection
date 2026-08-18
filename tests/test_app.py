"""
Automated Test Suite for AML Shield Web Application.

Includes unit tests for feature engineering vector alignment, model prediction wrappers,
single prediction scenarios (Scenario A Normal vs Scenario B Suspicious), and batch CSV processing.
"""

import os
import io
import sys
import pytest
import numpy as np
import pandas as pd

# Ensure root directory is accessible for pytest import
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.feature_engineering import transform_transaction, extract_feature_vector, EXACT_FEATURE_NAMES
from app.models import AMLModelWrapper, OPTIMAL_THRESHOLD
from scripts.generate_mock_model import generate_mock_artifacts

@pytest.fixture
def app():
    """Create Flask application fixture configured for testing."""
    models_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'models'))
    generate_mock_artifacts(models_dir)
    
    app_instance = create_app({'TESTING': True})
    yield app_instance

@pytest.fixture
def client(app):
    """Create test client for HTTP requests."""
    return app.test_client()

# ==============================================================================
# 1. UNIT TESTS: Feature Engineering Pipeline (46 Exact Features)
# ==============================================================================

def test_feature_transform_numeric_calculations():
    """Test log scalings, discrepancy, and flag engineering."""
    raw_tx = {
        'amount_paid': 100.0,
        'amount_received': 90.0,
        'payment_currency': 'US Dollar',
        'receiving_currency': 'Euro',
        'from_bank': 'Bank_A',
        'to_bank': 'Bank_B',
        'from_account': 'ACC_1',
        'to_account': 'ACC_2',
        'payment_format': 'Wire Transfer',
        'hour_of_day': 14,
        'day_of_week': 3
    }
    
    features = transform_transaction(raw_tx)
    
    assert np.isclose(features['log_amount_paid'], np.log1p(100.0))
    assert np.isclose(features['log_amount_received'], np.log1p(90.0))
    assert np.isclose(features['amount_discrepancy'], 10.0)
    assert features['currency_mismatch'] == 1
    assert features['cross_bank'] == 1
    assert features['self_loop'] == 0
    assert features['fmt_Wire Transfer'] == 1
    assert features['fmt_ACH'] == 0
    assert features['cur_Euro'] == 1
    assert features['cur_US Dollar'] == 0

def test_feature_vector_length_and_ordering():
    """Test feature vector extraction matches EXACT length (46) and order of EXACT_FEATURE_NAMES."""
    raw_tx = {
        'amount_paid': 5000.0,
        'payment_currency': 'US Dollar',
        'receiving_currency': 'US Dollar',
        'from_bank': 'Bank_A',
        'to_bank': 'Bank_A'
    }
    
    df_vector = extract_feature_vector(raw_tx, EXACT_FEATURE_NAMES)
    
    assert isinstance(df_vector, pd.DataFrame)
    assert df_vector.shape == (1, len(EXACT_FEATURE_NAMES))
    assert list(df_vector.columns) == EXACT_FEATURE_NAMES

def test_feature_engineering_null_handling():
    """Ensure feature engineering handles completely empty or missing inputs gracefully."""
    empty_tx = {}
    features = transform_transaction(empty_tx)
    
    assert features['log_amount_paid'] == 0.0
    assert features['amount_discrepancy'] == 0.0
    assert features['currency_mismatch'] == 0
    assert features['cross_bank'] == 0

# ==============================================================================
# 2. UNIT TESTS: Scenario A & Scenario B Differentiation
# ==============================================================================

def test_scenario_a_normal_transaction(client):
    """Scenario A: Normal transaction should return LOW risk score (< 0.25)."""
    payload = {
        'amount_paid': 45.50,
        'amount_received': 45.50,
        'payment_currency': 'US Dollar',
        'receiving_currency': 'US Dollar',
        'from_bank': '001',
        'to_bank': '002',
        'from_account': '8000F4580',
        'to_account': '8000F5340',
        'payment_format': 'Credit Card',
        'hour_of_day': 14,
        'day_of_week': 3
    }
    
    res = client.post('/predict', json=payload)
    assert res.status_code == 200
    json_data = res.get_json()
    
    pred = json_data['prediction']
    assert pred['risk_score'] < 0.25
    assert pred['is_suspicious'] is False
    assert pred['alert_level'] == 'Low'

def test_scenario_b_suspicious_transaction(client):
    """Scenario B: Structuring/Cross-currency/Self-loop transaction should return HIGH risk (>= 0.50)."""
    payload = {
        'amount_paid': 9999.99,
        'amount_received': 9999.99,
        'payment_currency': 'US Dollar',
        'receiving_currency': 'Euro',
        'from_bank': '010',
        'to_bank': '010',
        'from_account': '8000EBD30',
        'to_account': '8000EBD30',
        'payment_format': 'Reinvestment',
        'hour_of_day': 3,
        'day_of_week': 6
    }
    
    res = client.post('/predict', json=payload)
    assert res.status_code == 200
    json_data = res.get_json()
    
    pred = json_data['prediction']
    assert pred['risk_score'] >= 0.50
    assert pred['is_suspicious'] is True
    assert pred['alert_level'] == 'High'

# ==============================================================================
# 3. INTEGRATION TESTS: Flask Single & History Endpoints
# ==============================================================================

def test_index_route(client):
    """Test index dashboard renders successfully."""
    res = client.get('/')
    assert res.status_code == 200
    assert b"AML SHIELD" in res.data
    assert b"Transaction Details" in res.data

def test_health_endpoint(client):
    """Test system health endpoint returns 200 OK and model status."""
    res = client.get('/health')
    assert res.status_code == 200
    json_data = res.get_json()
    assert json_data['status'] == 'healthy'
    assert json_data['optimal_threshold'] == 0.50

def test_predict_endpoint_valid_payload(client):
    """Test POST /predict API endpoint with valid transaction JSON."""
    payload = {
        'from_bank': 'Bank_Alpha',
        'from_account': 'ACC_1001',
        'to_bank': 'Bank_Beta',
        'to_account': 'ACC_2002',
        'amount_paid': 15000.0,
        'payment_currency': 'US Dollar',
        'amount_received': 15000.0,
        'receiving_currency': 'US Dollar',
        'payment_format': 'Wire Transfer',
        'hour_of_day': 10,
        'day_of_week': 1
    }
    
    res = client.post('/predict', json=payload)
    assert res.status_code == 200
    json_data = res.get_json()
    
    assert json_data['success'] is True
    assert 'prediction' in json_data
    assert 'risk_score' in json_data['prediction']
    assert 'audit_entry' in json_data

def test_predict_endpoint_invalid_payload(client):
    """Test POST /predict handles negative amounts with 400 Bad Request."""
    payload = {'amount_paid': -500.0}
    res = client.post('/predict', json=payload)
    assert res.status_code == 400
    json_data = res.get_json()
    assert json_data['success'] is False
    assert "cannot be negative" in json_data['error']

def test_history_endpoint(client):
    """Test GET /api/history returns recorded audit trail."""
    res = client.get('/api/history')
    assert res.status_code == 200
    json_data = res.get_json()
    assert json_data['success'] is True
    assert 'history' in json_data

def test_export_csv_endpoint(client):
    """Test GET /export-csv triggers CSV file download."""
    payload = {'amount_paid': 1000.0}
    client.post('/predict', json=payload)
    
    res = client.get('/export-csv')
    assert res.status_code == 200
    assert res.mimetype == 'text/csv'

# ==============================================================================
# 4. INTEGRATION TESTS: Batch Prediction & CSV Upload Endpoints
# ==============================================================================

def test_batch_page_route(client):
    """Test GET /batch renders batch prediction dashboard successfully."""
    res = client.get('/batch')
    assert res.status_code == 200
    assert b"Batch Transaction Risk Engine" in res.data
    assert b"Upload CSV Dataset" in res.data

def test_download_sample_csv_endpoint(client):
    """Test GET /download-sample-csv streams sample template file."""
    res = client.get('/download-sample-csv')
    assert res.status_code == 200
    assert res.mimetype == 'text/csv'
    assert b"amount_paid,amount_received" in res.data

def test_batch_predict_valid_csv(client):
    """Test POST /api/batch-predict with valid CSV multipart upload."""
    csv_data = (
        "amount_paid,amount_received,payment_currency,receiving_currency,from_bank,to_bank,from_account,to_account,payment_format,hour_of_day,day_of_week\n"
        "45.50,45.50,US Dollar,US Dollar,001,002,8000F4580,8000F5340,Credit Card,14,3\n"
        "9999.99,9999.99,US Dollar,Euro,010,010,8000EBD30,8000EBD30,Reinvestment,3,6\n"
    )
    
    data = {
        'file': (io.BytesIO(csv_data.encode('utf-8')), 'test_batch.csv')
    }
    
    res = client.post('/api/batch-predict', data=data, content_type='multipart/form-data')
    assert res.status_code == 200
    json_data = res.get_json()
    
    assert json_data['success'] is True
    assert 'summary' in json_data
    assert json_data['summary']['total_transactions'] == 2
    assert 'predictions' in json_data
    assert len(json_data['predictions']) == 2
    
    # Check Scenario A (row 1) vs Scenario B (row 2) in batch
    p1 = json_data['predictions'][0]
    p2 = json_data['predictions'][1]
    
    assert p1['risk_score'] < 0.25
    assert p1['alert_level'] == 'Low'
    
    assert p2['risk_score'] >= 0.50
    assert p2['alert_level'] == 'High'
