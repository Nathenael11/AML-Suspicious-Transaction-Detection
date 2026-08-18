"""
Utility Functions for Validation, Logging, Audit Trail, and CSV Storage.

Provides input validation for transaction requests, application logging configuration,
persistent prediction audit logging in CSV format, and batch CSV file validation.
"""

import os
import csv
import io
import logging
from datetime import datetime, timezone
import pandas as pd

# Paths for application runtime data
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(BASE_DIR, 'logs')
DATA_DIR = os.path.join(BASE_DIR, 'data')

LOG_FILE = os.path.join(LOG_DIR, 'app.log')
PREDICTIONS_CSV = os.path.join(DATA_DIR, 'predictions.csv')

MAX_CSV_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
MAX_CSV_ROWS = 10000

REQUIRED_CSV_COLUMNS = [
    'amount_paid', 'amount_received', 'payment_currency', 'receiving_currency',
    'from_bank', 'to_bank', 'from_account', 'to_account', 'payment_format'
]

def setup_logging():
    """Configure structured logging to console and file."""
    os.makedirs(LOG_DIR, exist_ok=True)
    
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Avoid adding duplicate handlers if already configured
    if logger.handlers:
        return logger
        
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File Handler
    file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    
    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    logger.addHandler(console_handler)
    
    return logger

def validate_transaction_payload(payload: dict) -> tuple[bool, str]:
    """
    Validate incoming single JSON transaction payload.
    
    Returns (is_valid: bool, error_message: str).
    """
    if not isinstance(payload, dict):
        return False, "Payload must be a valid JSON object."
        
    # Check numeric fields
    if 'amount_paid' in payload:
        try:
            val = float(payload['amount_paid'])
            if val < 0:
                return False, "Amount paid cannot be negative."
        except (ValueError, TypeError):
            return False, "Amount paid must be a valid numeric value."
            
    if 'amount_received' in payload:
        try:
            val = float(payload['amount_received'])
            if val < 0:
                return False, "Amount received cannot be negative."
        except (ValueError, TypeError):
            return False, "Amount received must be a valid numeric value."
            
    return True, ""

def validate_csv_file(file_storage) -> tuple[bool, str, pd.DataFrame | None]:
    """
    Validate uploaded CSV file for batch inference.
    Checks extension, file size (<= 10MB), required header columns, and row limit (<= 10,000).
    
    Returns (is_valid: bool, error_message: str, df: pd.DataFrame | None).
    """
    if not file_storage or not file_storage.filename:
        return False, "No file provided in request.", None

    filename = file_storage.filename.lower()
    if not filename.endswith('.csv'):
        return False, "Invalid file format. Only CSV files (.csv) are supported.", None

    # Read bytes to check file size
    file_bytes = file_storage.read()
    if len(file_bytes) == 0:
        return False, "Uploaded CSV file is empty.", None

    if len(file_bytes) > MAX_CSV_SIZE_BYTES:
        return False, f"File size exceeds maximum allowed limit of 10MB ({len(file_bytes) / 1024 / 1024:.2f} MB provided).", None

    try:
        df = pd.read_csv(io.BytesIO(file_bytes))
    except Exception as e:
        return False, f"Failed to parse CSV file: {str(e)}", None

    if df.empty:
        return False, "Uploaded CSV file contains no data rows.", None

    if len(df) > MAX_CSV_ROWS:
        return False, f"CSV contains {len(df)} rows, exceeding the maximum allowed limit of 10,000 rows per batch.", None

    # Normalize column names for validation (lowercase, stripped)
    df_cols = [str(c).strip().lower() for c in df.columns]
    df.columns = df_cols

    missing_cols = [col for col in REQUIRED_CSV_COLUMNS if col not in df_cols]
    if missing_cols:
        return False, f"CSV is missing required column(s): {', '.join(missing_cols)}", None

    return True, "", df

def record_prediction_audit(raw_tx: dict, prediction_result: dict) -> dict:
    """
    Log prediction entry into audit CSV file (data/predictions.csv).
    
    Returns recorded audit record dictionary.
    """
    os.makedirs(DATA_DIR, exist_ok=True)
    
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    
    audit_entry = {
        'timestamp': timestamp,
        'from_bank': raw_tx.get('from_bank', 'Unknown'),
        'from_account': raw_tx.get('from_account', 'Unknown'),
        'to_bank': raw_tx.get('to_bank', 'Unknown'),
        'to_account': raw_tx.get('to_account', 'Unknown'),
        'amount_paid': raw_tx.get('amount_paid', 0.0),
        'payment_currency': raw_tx.get('payment_currency', 'USD'),
        'amount_received': raw_tx.get('amount_received', 0.0),
        'receiving_currency': raw_tx.get('receiving_currency', 'USD'),
        'payment_format': raw_tx.get('payment_format', 'Wire'),
        'risk_score': prediction_result.get('risk_score', 0.0),
        'is_suspicious': prediction_result.get('is_suspicious', False),
        'alert_level': prediction_result.get('alert_level', 'Low'),
        'threshold': prediction_result.get('threshold', 0.97)
    }
    
    file_exists = os.path.exists(PREDICTIONS_CSV)
    
    try:
        with open(PREDICTIONS_CSV, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=audit_entry.keys())
            if not file_exists:
                writer.writeheader()
            writer.writerow(audit_entry)
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to record prediction audit to CSV: {e}")
        
    return audit_entry

def get_prediction_history(limit=100) -> list[dict]:
    """Retrieve last N prediction entries from data/predictions.csv."""
    if not os.path.exists(PREDICTIONS_CSV):
        return []
        
    try:
        df = pd.read_csv(PREDICTIONS_CSV)
        if df.empty:
            return []
        df_recent = df.tail(limit).iloc[::-1]  # Most recent first
        return df_recent.to_dict(orient='records')
    except Exception as e:
        logging.getLogger(__name__).error(f"Error reading prediction history: {e}")
        return []
