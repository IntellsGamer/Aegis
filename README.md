# AEGIS — Digital Trust & Anti-Scam Platform

A full-stack monolith that scans URLs, emails, text, images, QR codes and files
for scams and phishing, producing a trust score, findings, a shareable map, and
PDF reports.

## Stack

- **Backend:** Python 3.12 · Flask 3 · SQLAlchemy 2 · Pydantic 2
- **Frontend:** server-rendered Jinja2 + vanilla JS, PWA-ready, no build step
- **AI/ML:** on-device scikit-learn + xgboost engines, tesseract OCR, zxing QR
- **Infra:** SQLite (dev) / PostgreSQL (prod), Redis + Celery workers, gunicorn

## Quick start

```bash
cd backend
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
sudo apt-get install -y tesseract-ocr   # OCR engine
python run.py                            # http://localhost:8000
```

Seeded admin: `admin@aegis.local` / `Admin@2024!`

## Test

```bash
python -m pytest -q          # unit/integration suite
python smoke_test.py         # end-to-end boot + auth + scan flow
```

## Production (Docker)

```bash
AEGIS_SECRET_KEY=<long-random> docker compose up --build
```

Reverse proxy via `nginx.conf`; app listens on `:8000`, healthcheck at
`/api/v1/health`.

## Layout

- `backend/app/` — Flask app factory, routes, services, models, schemas
- `backend/app/trust_engine/` — scoring/verdict logic (tunable DB rules)
- `backend/app/ai/` — ML text/url classifiers
- `backend/app/static/` + `backend/app/templates/` — UI
- `backend/tests/` — pytest suite · `backend/smoke_test.py` — smoke test
- `backend/alembic/` — DB migrations (baseline not yet generated)
- `backend/app/workers/` — Celery tasks (weekly digests)

## Security notes

- Signed session cookies, JWT access/refresh pair, bcrypt password hashing
- CSRF protection + per-route rate limiting (bypassed in TESTING)
- CSP, HSTS, frame/clickjack protection headers on every response
