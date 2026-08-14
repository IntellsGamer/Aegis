# Running AEGIS Natively on Windows

**Audience:** Windows 10/11 developers and operators who want to run AEGIS without WSL or a Linux container. The supported native path uses Python, SQLite, and the included PowerShell scripts. Redis, Celery, PostgreSQL, and Docker are not required for the core application workflow.

## Prerequisites

| Component | Required | Purpose |
|---|---:|---|
| Python 3.12 with the Python Launcher (`py`) | Yes | Creates and runs the project virtual environment |
| PowerShell 5.1 or newer | Yes | Runs the supplied setup and start scripts |
| Tesseract OCR | Optional | Extracts text from uploaded images; core text, URL, email, QR, file, and reporting workflows still run without it |
| Redis, Celery, PostgreSQL, Docker Desktop | Optional | Production-scale or background-service infrastructure, not required for native local use |

> **Security note:** the native Windows launcher is suitable for local development. If you use `-Production`, set a unique `AEGIS_SECRET_KEY` first and place the application behind appropriate TLS and network controls.

## One-Time Setup

Open PowerShell in the repository root and run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup-windows.ps1
```

The script creates `backend\.venv`, upgrades `pip`, and installs the dependencies appropriate for Windows. In particular, it installs Waitress instead of Gunicorn for native Windows serving.

If you do not intend to use image OCR immediately, pass `-SkipOcr`:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup-windows.ps1 -SkipOcr
```

## Start the Application

Use either PowerShell or the supplied `.cmd` launcher:

```powershell
.\scripts\run-windows.ps1
```

```text
scripts\run-windows.cmd
```

Then open [http://localhost:8000](http://localhost:8000). The first development startup uses SQLite at `backend\aegis.db`, so no database server is needed.

| Mode | Command | Server behavior |
|---|---|---|
| Development | `.\scripts\run-windows.ps1` | Starts the Flask development server with reload support |
| Native Windows production | `$env:AEGIS_SECRET_KEY = "<long-random-secret>"; .\scripts\run-windows.ps1 -Production` | Starts Waitress, a Windows-compatible WSGI server |
| Linux/container production | `docker compose up --build` | Keeps the existing Gunicorn, Redis, Celery, and PostgreSQL deployment path |

## Optional Image OCR

Install Tesseract for Windows, then either add its installation directory to your `PATH` or configure the exact executable for the current PowerShell session:

```powershell
$env:AEGIS_TESSERACT_CMD = "C:\Program Files\Tesseract-OCR\tesseract.exe"
.\scripts\run-windows.ps1
```

AEGIS reads `AEGIS_TESSERACT_CMD` at startup and passes the executable to `pytesseract`. When Tesseract is unavailable, only image text extraction is affected. The UI/API returns a clear guidance message instead of preventing the application from starting.

## Validation

Run the portable automated suite from PowerShell after setup:

```powershell
Set-Location backend
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe smoke_test.py
```

The smoke test intentionally sets `AEGIS_OCR_ENGINE=none`, which keeps the core validation path independent of a system OCR binary. GitHub Actions also runs this suite on both Ubuntu and Windows.

## Troubleshooting

| Symptom | Resolution |
|---|---|
| `Python Launcher was not found` | Reinstall Python 3.12, select the PATH option, and confirm `py -3.12 --version` works in a new terminal. |
| `Tesseract executable does not exist` | Correct `AEGIS_TESSERACT_CMD`, or add the directory containing `tesseract.exe` to `PATH`, then restart AEGIS. |
| Image scan says no OCR engine is available | Install/configure Tesseract, or leave OCR disabled if image text extraction is not needed. QR decoding remains separately available through its Python package. |
| Port 8000 is in use | Set `AEGIS_PORT` to a free port before launching, such as `$env:AEGIS_PORT = "8080"`. |
| Production launcher refuses to start | Set a unique `AEGIS_SECRET_KEY`; the default development secret is deliberately rejected. |
