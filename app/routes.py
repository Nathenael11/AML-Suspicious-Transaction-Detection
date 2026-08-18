"""
Flask Route Handlers and API Endpoints.

Defines HTTP routes for dashboard UI serving, single & batch transaction risk prediction,
audit history, CSV result export, and system health checks.
"""

import os
import time
import logging
from flask import Blueprint, render_template, request, jsonify, send_file, current_app
from app.models import AMLModelWrapper
from app.utils import (
    validate_transaction_payload,
    validate_csv_file,
    record_prediction_audit,
    get_prediction_history,
    PREDICTIONS_CSV,
    BASE_DIR
)

logger = logging.getLogger(__name__)

bp = Blueprint('main', __name__)

# Global model instance placeholder (initialized in create_app)
model_wrapper = None

def get_model():
    """Retrieve or lazy-load model wrapper instance."""
    global model_wrapper
    if model_wrapper is None:
        model_wrapper = AMLModelWrapper()
    return model_wrapper

@bp.route('/')
def index():
    """Render main AML Shield single prediction dashboard UI."""
    return render_template('index.html')

@bp.route('/batch')
def batch():
    """Render AML Shield batch CSV prediction page."""
    return render_template('batch.html')

@bp.route('/download-sample-csv')
def download_sample_csv():
    """Provide downloadable sample CSV template for batch prediction."""
    try:
        sample_path = os.path.join(BASE_DIR, 'static', 'sample_batch.csv')
        if not os.path.exists(sample_path):
            return jsonify({'success': False, 'error': 'Sample CSV file not found'}), 404
        return send_file(
            sample_path,
            mimetype='text/csv',
            as_attachment=True,
            download_name='aml_sample_batch_template.csv'
        )
    except Exception as e:
        logger.error(f"Error downloading sample CSV: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/predict', methods=['POST'])
def predict():
    """
    API Endpoint: Evaluate single transaction risk using trained XGBoost model.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Missing request JSON body'}), 400

        # Input validation
        is_valid, err_msg = validate_transaction_payload(data)
        if not is_valid:
            return jsonify({'success': False, 'error': err_msg}), 400

        # Execute prediction
        model = get_model()
        prediction = model.predict(data)

        # Audit log to CSV
        audit_entry = record_prediction_audit(data, prediction)

        logger.info(
            f"Prediction calculated: Amount=${data.get('amount_paid', 0)} | "
            f"Risk Score={prediction['risk_score']} | Alert={prediction['alert_level']}"
        )

        return jsonify({
            'success': True,
            'prediction': prediction,
            'audit_entry': audit_entry
        }), 200

    except Exception as e:
        logger.error(f"Prediction endpoint error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': f"Internal server error: {str(e)}"}), 500

@bp.route('/api/batch-predict', methods=['POST'])
def batch_predict():
    """
    API Endpoint: Execute batch prediction on uploaded CSV file.
    Expects multipart form data with file field 'file'.
    """
    t_start = time.time()
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file part in request. Please upload a file with key "file".'}), 400

        file_storage = request.files['file']
        is_valid, err_msg, df = validate_csv_file(file_storage)
        if not is_valid or df is None:
            return jsonify({'success': False, 'error': err_msg}), 400

        model = get_model()
        predictions = []
        
        high_risk_count = 0
        med_risk_count = 0
        low_risk_count = 0
        total_score_sum = 0.0

        # Process each row
        for idx, row in df.iterrows():
            # Build raw_tx payload dict from CSV row
            raw_tx = {
                'amount_paid': row.get('amount_paid', 0.0),
                'amount_received': row.get('amount_received', row.get('amount_paid', 0.0)),
                'payment_currency': str(row.get('payment_currency', 'USD')),
                'receiving_currency': str(row.get('receiving_currency', 'USD')),
                'from_bank': str(row.get('from_bank', 'Unknown')),
                'to_bank': str(row.get('to_bank', 'Unknown')),
                'from_account': str(row.get('from_account', 'Unknown')),
                'to_account': str(row.get('to_account', 'Unknown')),
                'payment_format': str(row.get('payment_format', 'Wire')),
                'hour_of_day': row.get('hour_of_day', None),
                'day_of_week': row.get('day_of_week', None)
            }

            pred = model.predict(raw_tx)
            
            score = pred['risk_score']
            alert_level = pred['alert_level']
            total_score_sum += score

            if alert_level == 'High':
                high_risk_count += 1
            elif alert_level == 'Medium':
                med_risk_count += 1
            else:
                low_risk_count += 1

            record_prediction_audit(raw_tx, pred)

            predictions.append({
                'row_number': idx + 1,
                'from_account': f"{raw_tx['from_bank']}:{raw_tx['from_account']}",
                'to_account': f"{raw_tx['to_bank']}:{raw_tx['to_account']}",
                'amount_paid': raw_tx['amount_paid'],
                'payment_currency': raw_tx['payment_currency'],
                'amount_received': raw_tx['amount_received'],
                'receiving_currency': raw_tx['receiving_currency'],
                'payment_format': raw_tx['payment_format'],
                'risk_score': score,
                'is_suspicious': pred['is_suspicious'],
                'alert_level': alert_level,
                'action_recommendation': pred['action_recommendation']
            })

        total_rows = len(predictions)
        avg_score = round(total_score_sum / total_rows, 4) if total_rows > 0 else 0.0
        elapsed_sec = round(time.time() - t_start, 3)

        summary = {
            'total_transactions': total_rows,
            'high_risk_count': high_risk_count,
            'medium_risk_count': med_risk_count,
            'low_risk_count': low_risk_count,
            'high_risk_percentage': round((high_risk_count / total_rows) * 100, 1) if total_rows > 0 else 0.0,
            'average_risk_score': avg_score,
            'processing_time_seconds': elapsed_sec
        }

        logger.info(f"Batch prediction completed: {total_rows} rows processed in {elapsed_sec}s. High Risk: {high_risk_count}")

        return jsonify({
            'success': True,
            'summary': summary,
            'predictions': predictions
        }), 200

    except Exception as e:
        logger.error(f"Batch prediction error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': f"Internal server error processing batch: {str(e)}"}), 500

@bp.route('/api/history', methods=['GET'])
def history():
    """API Endpoint: Retrieve recent transaction prediction history (last 100)."""
    try:
        limit = request.args.get('limit', default=100, type=int)
        records = get_prediction_history(limit=limit)
        return jsonify({'success': True, 'count': len(records), 'history': records}), 200
    except Exception as e:
        logger.error(f"Error fetching history: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/export-csv', methods=['GET'])
def export_csv():
    """Export all prediction audit logs as a downloadable CSV file."""
    try:
        if not os.path.exists(PREDICTIONS_CSV):
            return jsonify({'success': False, 'error': 'No prediction records found yet.'}), 404

        return send_file(
            PREDICTIONS_CSV,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f"aml_predictions_export_{request.args.get('ts', 'all')}.csv"
        )
    except Exception as e:
        logger.error(f"Error exporting CSV: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/health', methods=['GET'])
def health():
    """System Health Check endpoint."""
    model = get_model()
    return jsonify({
        'status': 'healthy',
        'service': 'AML Shield Transaction Detector',
        'model_loaded': model.model is not None,
        'is_mock_model': model.is_mock,
        'features_count': len(model.feature_names),
        'optimal_threshold': model.threshold
    }), 200
