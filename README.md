# 🛡️ AML Shield - Suspicious Transaction Detection

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/framework-Flask--3.0-green.svg)](https://flask.palletsprojects.com/)
[![XGBoost](https://img.shields.io/badge/model-XGBoost--2.0-orange.svg)](https://xgboost.readthedocs.io/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/license-MIT-brightgreen.svg)](LICENSE)

**AML Shield** is a web application I built for my Cyber Talent Center(CTC) project. It uses an XGBoost machine learning model trained on the IBM AML dataset (5.07 million transactions) to detect suspicious money laundering patterns.

The model uses **56 features** including transaction amounts, currency mismatches, bank transfers, time-based signals, and graph features like account connections, transaction cycles, and velocity patterns.

🌐 **Live Demo:** [https://aml-suspicious-transaction-detection.onrender.com](https://aml-suspicious-transaction-detection.onrender.com)

📁 **GitHub:** [https://github.com/Nathenael11/AML-Suspicious-Transaction-Detection](https://github.com/Nathenael11/AML-Suspicious-Transaction-Detection)

---

## 📊 Key Features

- **Real-time Analysis** - Submit a transaction and get an instant risk score
- **Batch Upload** - Upload CSV files for bulk transaction analysis
- **Risk Scorecard** - Visual gauge showing risk level (0-1)
- **Audit History** - Last 100 predictions stored with timestamps
- **Export to CSV** - Download prediction history for reporting
- **Dark Theme UI** - Professional dark navy and teal design

---

## 📸 Screenshots

### Dashboard
![Dashboard](images/dashboard.png)

### Normal Transaction (Low Risk)
![Normal Transaction](images/normal.png)

### Suspicious Transaction (High Risk)
![Suspicious Transaction](images/suspicious.png)

### Batch Upload
![Batch Upload](images/batch.png)

### Audit History
![Audit History](images/audit.png)

---

## Performance Results

| Metric | Baseline Model | Full Model (Graph-Enhanced) | Improvement |
|--------|----------------|----------------------------|-------------|
| **PR-AUC** | 0.0133 | **0.1180** | **+386%** |
| **F1 Score** | 0.0376 | **0.1828** | **+386%** |
| **Precision** | 3.4% | **14.6%** | +11.2% |
| **Recall** | 4.2% | **24.5%** | +20.3% |
| **Top-100 Precision** | — | **36%** | — |
| **Dataset Size** | 5.07M | 5.07M | — |
| **Positive Rate** | 0.1% | 0.1% | — |

### What These Numbers Mean:
- **PR-AUC 0.1180** - The model is 9x better than random guessing (random would be ~0.001)
- **14.6% Precision** - About 1 in 7 flagged transactions is actually laundering
- **24.5% Recall** - Catches about 1 in 4 laundering cases
- **36% Top-100 Precision** - In the top 100 riskiest accounts, 36 are confirmed launderers

---

## 🏗 Architecture
User → Web Dashboard → Flask API → Feature Engineering (56 features) → XGBoost Model → Risk Score


---

## 🛠 Quick Start

```bash
# Clone the repository
git clone https://github.com/Nathenael11/AML-Suspicious-Transaction-Detection.git
cd aml-webapp

# Install dependencies
pip install -r requirements.txt

# Run the app
python run.py

# Open browser to http://localhost:5000

🐳 Run with Docker

docker build -t aml-shield .
docker run -p 5000:5000 aml-shield

📁 Project Structure
aml-webapp/
├── app/           # Flask backend (routes, models, feature engineering)
├── static/        # CSS, JavaScript, logo
├── templates/     # HTML dashboard
├── models/        # Trained XGBoost model files
├── tests/         # Unit tests
├── run.py         # Entry point
├── Dockerfile     # Container setup
└── requirements.txt

🧪 Running Tests
pytest tests/ -v

📡 API Endpoints
Endpoint	Method	Description
/	GET	Web interface
/predict	POST	Analyze a transaction
/api/history	GET	Get prediction history
/export-csv	GET	Download predictions
/health	GET	Check service status

🧰 Technologies Used
Backend: Python, Flask, XGBoost, Scikit-Learn, Pandas, NumPy

Frontend: HTML5, CSS3, JavaScript

DevOps: Docker, GitHub Actions

Deployment: Render.com

📄 License
MIT License - see LICENSE file for details.

🙏 Acknowledgments
IBM for the AML dataset

XGBoost library developers

Flask framework team
course Mentor Mr.Mikiyas Tadesse

## Author
Nathenael Ermias

