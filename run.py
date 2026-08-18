"""
Root Application Runner for AML Shield Web Application.

Run using:
    python run.py
"""

import sys
import os

# Ensure root directory is on sys.path
root_dir = os.path.dirname(os.path.abspath(__file__))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from app import create_app

app = create_app()

if __name__ == '__main__':
    print("=" * 65)
    print("  AML Shield Transaction Detection Web Application")
    print("  XGBoost Model Pipeline Loaded | Optimal Threshold: 0.97")
    print("  Server running on http://127.0.0.1:5000")
    print("=" * 65)
    app.run(host='0.0.0.0', port=5000, debug=True)
