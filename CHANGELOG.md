# Changelog

All notable changes to the AML Shield Transaction Detection project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-08-18

### Added
- Complete Flask REST API backend with modular structure (`app/__init__.py`, `app/routes.py`, `app/models.py`, `app/utils.py`).
- 56-feature pipeline in `app/feature_engineering.py` matching exact notebook logic (log amount scaling, currency mismatch, cross-bank flags, 24h rolling totals, fan-in/fan-out graph metrics, z-scores, and cycle flags).
- Thread-safe `AMLModelWrapper` for XGBoost model evaluation with PR-AUC tuned threshold of `0.97`.
- Interactive web dashboard UI with dark navy/teal aesthetic, risk score radial meter, color-coded alert badges, action recommendations, and audit table.
- Real-time audit trail persistent logging to `data/predictions.csv`.
- CSV export endpoint (`GET /export-csv`).
- Production Docker multi-stage build (`Dockerfile`) and Docker Compose orchestrator (`docker-compose.yml`).
- AWS EC2 automated deployment script (`deploy.sh`).
- Automated CI/CD workflow (`.github/workflows/deploy.yml`).
- Unit and integration tests (`tests/test_app.py`).
