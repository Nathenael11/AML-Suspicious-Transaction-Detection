# 🛡️ AML Shield — Transaction Detection System

![Python](https://img.shields.io/badge/Python-3.10-blue)
![Flask](https://img.shields.io/badge/Flask-2.x-black)
![XGBoost](https://img.shields.io/badge/XGBoost-2.x-red)
![Docker](https://img.shields.io/badge/Docker-ready-blue)

## Overview

AML Shield is a web application I built for my ctc project. It uses an
XGBoost model trained on the IBM AML dataset (5.07 million transactions) to
flag transactions that look like money laundering. You submit a transaction
(or a batch of them via CSV) and it returns a risk score along with the
features that drove the decision. It's meant for anyone who wants to see how
graph-based features can be applied to financial fraud detection — a student
project, not a production compliance tool.

**Live demo:** https://aml-suspicious-transaction-detection.onrender.com
**Repo:** https://github.com/Nathenael11/AML-Suspicious-Transaction-Detection

> Note: this is hosted on Render's free tier, so the first request after a
> while can take 30-60 seconds to wake the server up. That's normal, not a bug.

## Key Features

- Real-time single-transaction risk scoring
- Batch analysis via CSV upload
- Risk score shown as a gauge, not just a raw number
- Audit history of past checks
- Export results back out to CSV
- Dark theme UI

## Performance

Trained and evaluated on the HI-Small variant of the IBM AML dataset, with a
strict chronological train/val/test split (no random shuffling — the model
never sees "future" transactions during training). All numbers below are on
the held-out test set.

| Metric | Baseline (no graph features) | Full Model | Relative Improvement |
|---|---|---|---|
| PR-AUC | 0.0133 | 0.1180 | +787% |
| F1 Score | 0.0376 | 0.1828 | +386% |
| Precision | 3.4% | 14.6% | +329% |
| Recall | 4.2% | 24.5% | +483% |
| Top-100 Precision | — | 36% | — |

A few honest notes on these numbers:

- This is an extremely imbalanced dataset (illicit transactions are a
  fraction of a percent of the total), so precision and recall in the
  teens/twenties are actually in line with what's reported in the papers this
  dataset comes from — not a sign something's broken.
- The "baseline" model uses only raw transaction fields (amount, currency,
  timestamp, etc). The "full" model adds graph features — fan-in/fan-out per
  account, cycle detection, transaction velocity, and a few others. The
  consistent jump across every metric is basically the whole point of the
  project: individual transactions rarely look suspicious on their own, but
  the account's surrounding transaction pattern usually does.
- PR-AUC is the metric I'd actually trust here over accuracy — with this much
  class imbalance, a model that predicts "not laundering" every time would
  score over 99% accuracy and be useless.

## Architecture

```
User → Web UI (Flask templates) → Flask API
                                       │
                                       ▼
                          Feature Engineering
                (base transaction features + graph features:
                 fan-in/out, cycle membership, velocity, z-score)
                                       │
                                       ▼
                              XGBoost Model
                                       │
                                       ▼
                          Risk Score + Explanation
```

## Quick Start

```bash
git clone https://github.com/Nathenael11/AML-Suspicious-Transaction-Detection
cd aml-webapp
pip install -r requirements.txt
python run.py
```

The app runs locally on `http://localhost:5000` by default. If you just want
to try it without setting anything up, use the live demo link above instead.

## Project Structure

```
aml-webapp/
├── app/            # Flask application (routes, model loading, inference logic)
├── static/         # CSS, JS, images
├── templates/      # HTML templates
├── models/         # trained XGBoost model + feature metadata
├── requirements.txt
└── run.py
```

## Technologies Used

- **Backend:** Python, Flask
- **Model:** XGBoost
- **Frontend:** HTML, CSS, JavaScript
- **Deployment:** Docker, GitHub Actions, Render

## Limitations

Worth being upfront about, since this is a student project and not a
finished product:

- Trained on one dataset variant (HI-Small). Performance on a lower-illicit-ratio
  dataset would likely be worse — that's a documented property of this dataset
  family, not something specific to this implementation.
- Cycle detection is bounded (max path length, degree-capped) for the sake of
  runtime, so it will miss longer or more unusual laundering chains.
- A precision this low means a real deployment would still need a human
  reviewing flagged transactions, not acting on the score alone.

## Acknowledgments

- IBM for the AML dataset (Altman et al., "Realistic Synthetic Financial
  Transactions for Anti-Money Laundering Models")
- The XGBoost library
- Flask
## Author
 Nathenael Ermias
