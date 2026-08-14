# AEGIS — Evidence-First Digital Trust Analysis

AEGIS is a full-stack trust and anti-scam platform for URLs, emails, messages, images, QR codes, and uploaded files. It produces an explainable **trust score**, a risk level, the observable evidence behind that assessment, and practical next actions.

> **AEGIS does not train or run an LLM, transformer, statistical classifier, or opaque prediction model.** Its active predictor is a deterministic evidence-fusion engine. This makes results reproducible, inspectable, and deployable without a model lifecycle.

## Why Evidence Fusion

A phishing assessment should not be a flat sum of keywords. AEGIS groups correlated signals, applies diminishing returns to repeated phrases, preserves the detector confidence and evidence for every indicator, and increases risk only when **independent evidence families agree**. For example, an email-authentication failure, a credential request, and a deceptive link are stronger together than three variations of an urgency phrase. Confidence represents evidence coverage and agreement; it is not a claim that a verdict has been externally validated.

| Engine property | AEGIS behavior |
|---|---|
| Prediction method | Deterministic calibrated evidence fusion |
| Training required | None |
| Text interpretation | Multilingual curated pattern and request-context analysis |
| URL intelligence | Local lexical and structural analysis, plus optional live transport/page observations for URL scans |
| Correlation handling | Evidence-family grouping with diminishing returns |
| Explainability | Every visible impact is tied to a concrete finding and evidence snippet |
| Confidence | Derived from source reliability, coverage, diversity, and evidence agreement |

The evidence families reflect common anti-phishing red flags: independent verification of sender and link identity, urgency, deceptive URLs, unexpected requests for sensitive data, and email authentication results. CISA and NIST specifically emphasize urgent requests, suspicious shortened or misspelled links, credential/financial requests, and source verification as important signals.[1][2]

## Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12, Flask 3, SQLAlchemy 2, Pydantic 2 |
| Frontend | Server-rendered Jinja2, vanilla JavaScript, PWA-ready; no build step |
| Prediction | Deterministic evidence fusion, URL/page evidence, email authentication, and curated multilingual patterns |
| Infrastructure | SQLite for development; PostgreSQL/Redis/Celery/Gunicorn for Linux containers; Waitress for native Windows production |

## Quick Start

| Platform | Native local startup |
|---|---|
| **Windows 10/11** | Run `powershell -ExecutionPolicy Bypass -File .\\scripts\\setup-windows.ps1`, then ` .\\scripts\\run-windows.ps1` |
| **Linux / macOS** | Create a virtual environment in `backend`, install `requirements.txt`, then run `python run.py` |
| **Linux container / Windows Docker Desktop** | Run `AEGIS_SECRET_KEY=<long-random-secret> docker compose up --build` |

For a complete native Windows installation, optional Tesseract OCR configuration, production mode, and troubleshooting, see [the Windows guide](docs/windows.md). The core local application works without Redis, Celery, PostgreSQL, Docker, or OCR; image text extraction requires a Tesseract installation or configuration.

On Linux or macOS, the minimal native path is:

```bash
cd backend
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python run.py                            # http://localhost:8000
```

Set a unique `AEGIS_SECRET_KEY` and production database configuration before any deployment. The development seed account is intentionally limited to local development and must not be exposed publicly.

## Testing

```bash
cd backend
PYTHONPATH=. python -m pytest -q
PYTHONPATH=. python smoke_test.py

# Windows PowerShell
# .\\.venv\\Scripts\\python.exe -m pytest -q
# .\\.venv\\Scripts\\python.exe smoke_test.py
```

The focused evidence-engine tests demonstrate that benign topical language does not become a threat by itself, repeated related cues have diminishing influence, and independent hostile observations raise the verdict appropriately.

## Production

```bash
AEGIS_SECRET_KEY=<long-random-secret> docker compose up --build
```

The reverse proxy configuration is in `nginx.conf`; the application listens on `:8000` and exposes a health check at `/api/v1/health`.

## Layout

| Path | Purpose |
|---|---|
| `backend/app/trust_engine/` | Deterministic evidence-fusion scoring and tunable default rule registry |
| `backend/app/ai/link_analysis.py` | Local, no-network analysis for links embedded in messages and emails |
| `backend/app/services/` | URL, text, email, file, image, and QR acquisition and scan orchestration |
| `backend/app/static/` and `backend/app/templates/` | The PWA-ready server-rendered interface |
| `backend/tests/` | Unit, integration, and regression coverage |
| `docs/` | Architecture and validation notes |

## References

[1] [CISA, *Recognize and Report Phishing*](https://www.cisa.gov/secure-our-world/recognize-and-report-phishing)

[2] [NIST, *Phishing Guidance for Small Businesses*](https://www.nist.gov/itl/smallbusinesscyber/guidance-topic/phishing)
