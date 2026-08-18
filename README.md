# AML Shield - Production Anti-Money Laundering Detection System

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/framework-Flask--3.0-green.svg)](https://flask.palletsprojects.com/)
[![XGBoost](https://img.shields.io/badge/model-XGBoost--2.0-orange.svg)](https://xgboost.readthedocs.io/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/license-MIT-brightgreen.svg)](LICENSE)

**AML Shield** is a production-grade Anti-Money Laundering (AML) transaction risk detection application powered by an XGBoost machine learning model trained on over **5.07 million transactions**. The model incorporates a **56-feature pipeline** spanning transaction scaling, currency & bank mismatches, temporal signals, scatter-gather fan-in/out hub metrics, rolling 24-hour velocity totals, amount z-scores, and graph cycle membership detection.

---

## 🌟 Performance & Model Results Summary

| Metric | Baseline Model | AML Shield (Graph-Enhanced XGBoost) | Improvement |
| :--- | :--- | :--- | :--- |
| **PR-AUC (Precision-Recall)** | 0.158 | **0.768** | **+386% Boost** |
| **Top-100 Precision** | 14.0% | **36.0%** | **+157% Boost** |
| **Dataset Size** | 5.07M Transactions | 5.07M Transactions | — |
| **Positive Class Rate** | 0.1% (Imbalanced) | 0.1% (Scale Pos Weight Tuned) | — |
| **Optimal Threshold** | 0.50 | **0.97** | PR-AUC Tuned |

---

## 🏗 System Architecture Diagram

```
                             [ WEB DASHBOARD (HTML5 / Vanilla JS) ]
                                               │
                                       POST /predict (JSON)
                                               │
                                               ▼
                              [ FLASK REST API LAYER (app/routes.py) ]
                                               │
                                               ▼
                         [ FEATURE ENGINEERING PIPELINE (56 Features) ]
                       ├── Log Transformations (log1p Amount Paid/Received)
                       ├── Currency & Bank Mismatch Flags
                       ├── One-Hot Encodings (Payment Format & Currencies)
                       ├── 24-Hour Rolling Totals & Amount Z-Scores
                       └── Graph Topology (Degrees, Fan-In/Out Hubs, Cycles)
                                               │
                                               ▼
                             [ XGBOOST INFERENCE ENGINE (models/model.pkl) ]
                                               │
                                       Score vs 0.97 Threshold
                                               │
                         ┌─────────────────────┴─────────────────────┐
                         ▼                                           ▼
            [ High Risk / Suspicious ]                   [ Low Risk / Normal ]
             Alert Level: High                           Alert Level: Low
             Action: Freeze & SAR Filing                 Action: Pass
                         │                                           │
                         └─────────────────────┬─────────────────────┘
                                               │
                                               ▼
                             [ REAL-TIME AUDIT LOG (data/predictions.csv) ]
```

---

## 📸 Interface Preview (UI Mockup)

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│ 🛡 AML SHIELD  [XGBoost v1.0]                          🟢 Model Active | Thresh: 0.97 │
├──────────────────────────────────────────┬───────────────────────────────────────┤
│ 📝 Transaction Details                   │ 📊 Risk Analysis Scorecard            │
│ Sender Bank:    [ Bank_Alpha    ]        │                                       │
│ Sender Account: [ ACC_100928   ]        │              (  0.98  )               │
│ Amount Paid:    [ $49,000.00   ] USD     │            HIGH RISK (SUSPICIOUS)     │
│ Amount Recv:    [ $41,500.00   ] EUR     │                                       │
│ Format:         [ Wire Transfer ]        │ ⚠️ Action Recommendation:              │
│                                          │ Freeze account pending SAR filing &   │
│ [ ⚡ Run Risk Inference ]                 │ Level 2 Compliance Review.            │
├──────────────────────────────────────────┴───────────────────────────────────────┤
│ 📜 Audit History Trail (Last 100 Predictions)                 [ 📥 Export to CSV ] │
│ 2026-08-18 10:30 | ACC_HUB_99 ➔ ACC_RECV_44 | $49,000 | Score: 0.9812 | HIGH RISK  │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📂 Project Directory Structure

```
aml-webapp/
├── app/
│   ├── __init__.py           # Application Factory & Logging setup
│   ├── main.py               # Module direct launcher
│   ├── routes.py             # Flask HTTP endpoints (/predict, /api/history, /export-csv, /health)
│   ├── models.py             # XGBoost model wrapper & 0.97 threshold business logic
│   ├── utils.py              # Input validation, CSV audit logging, helper utilities
│   └── feature_engineering.py# 56-Feature engineering pipeline matching training notebook
├── static/
│   ├── css/
│   │   └── style.css         # Dark Navy & Teal accent styling, responsive grid & animations
│   ├── js/
│   │   └── script.js         # Interactive form logic, AJAX fetching, gauge animation, CSV export
│   └── img/
│       └── logo.svg          # AML Shield vector logo
├── templates/
│   └── index.html            # Single-page dashboard UI
├── models/
│   ├── model.pkl             # Trained XGBoost model artifact (User provided or auto-generated)
│   └── feature_names.pkl     # List of 56 feature names in exact vector sequence
├── tests/
│   └── test_app.py           # Unit tests for feature engineering, model wrapper, and API routes
├── scripts/
│   └── generate_mock_model.py# Helper script to create synthetic model for demonstration
├── data/
│   └── predictions.csv       # Persistent prediction audit records (auto-generated)
├── logs/
│   └── app.log               # Application execution log file (auto-generated)
├── .github/
│   └── workflows/
│       └── deploy.yml        # CI/CD automated test & deployment workflow
├── Dockerfile                # Multi-stage production Docker container definition
├── docker-compose.yml        # Local development Compose orchestrator
├── deploy.sh                 # Production deployment shell script for Linux/EC2
├── requirements.txt          # Python dependencies
├── run.py                    # Root entry point script (python run.py)
├── CHANGELOG.md              # Version release history
└── README.md                 # System documentation
```

---

## 🛠 Quickstart Setup Guide

### 1. Prerequisites
- Python 3.10+
- `pip` and `virtualenv`

### 2. Clone & Install
```bash
# Clone the repository
git clone https://github.com/your-org/aml-webapp.git
cd aml-webapp

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

### 3. Place Model Artifacts (Optional)
Place your trained XGBoost model and feature name files into the `models/` directory:
- `models/model.pkl`
- `models/feature_names.pkl`

*(Note: If these files are absent, the application automatically builds a high-fidelity synthetic model on boot for immediate testing).*

### 4. Run Application
```bash
python run.py
```
Open your browser and navigate to **`http://localhost:5000`**.

---

## 🧪 Running Automated Tests

Run the full pytest suite to verify feature extraction, model prediction, and API endpoints:
```bash
pytest tests/ -v
```

---

## 🐳 Docker Setup & Local Orchestration

### Using Docker Compose
```bash
docker-compose up --build
```
Access the application at `http://localhost:5000`.

### Manual Docker Build & Run
```bash
docker build -t aml-shield-webapp:latest .
docker run -d -p 5000:5000 --name aml-webapp aml-shield-webapp:latest
```

---

## 🚀 AWS EC2 Production Deployment

Deploy seamlessly to an AWS EC2 instance using the automated script:
```bash
chmod +x deploy.sh
./deploy.sh
```

---

## 📡 REST API Documentation

### 1. `POST /predict`
Evaluates money laundering risk for a single transaction.

**Request Header:** `Content-Type: application/json`

**Sample Payload:**
```json
{
  "from_bank": "Bank_Alpha",
  "from_account": "ACC_100928",
  "to_bank": "Bank_Offshore",
  "to_account": "ACC_RECV_44",
  "amount_paid": 49000.00,
  "payment_currency": "USD",
  "amount_received": 41500.00,
  "receiving_currency": "EUR",
  "payment_format": "Wire",
  "timestamp": "2026-08-18 10:30"
}
```

**Sample Response (200 OK):**
```json
{
  "success": true,
  "prediction": {
    "risk_score": 0.9812,
    "is_suspicious": true,
    "alert_level": "High",
    "threshold": 0.97,
    "action_recommendation": "IMMEDIATE ACTION REQUIRED: High probability of money laundering / structuring. Freeze account pending SAR (Suspicious Activity Report) filing and L2 Compliance review.",
    "features_extracted": 56
  },
  "audit_entry": {
    "timestamp": "2026-08-18 10:30:00",
    "from_bank": "Bank_Alpha",
    "from_account": "ACC_100928",
    "risk_score": 0.9812,
    "is_suspicious": true,
    "alert_level": "High"
  }
}
```

### 2. `GET /api/history?limit=100`
Fetches the last N prediction audit records.

### 3. `GET /export-csv`
Downloads the entire prediction history as a `.csv` file.

### 4. `GET /health`
Returns application uptime and model operational status.

---

## 🧰 Technologies Used

- **Machine Learning**: XGBoost, Scikit-Learn, Pandas, NumPy
- **Backend Framework**: Flask, Werkzeug, Gunicorn
- **Frontend Stack**: HTML5, Vanilla JavaScript (ES6+), CSS3 (Dark Navy/Teal)
- **DevOps & Testing**: Docker, Docker Compose, Pytest, GitHub Actions, Bash

---

## 📄 License
This project is licensed under the MIT License.
