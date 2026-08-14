<#
.SYNOPSIS
    Prepare a native Windows development environment for AEGIS.

.DESCRIPTION
    Requires the Python launcher with Python 3.12 installed. The script creates
    backend\.venv, upgrades pip, and installs the platform-appropriate package
    set. OCR remains optional: URL, text, email, QR, file, and report workflows
    operate without a Tesseract system installation.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\scripts\setup-windows.ps1
#>
[CmdletBinding()]
param(
    [switch]$SkipOcr
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$Backend = Join-Path $RepoRoot "backend"
$Python = Join-Path $Backend ".venv\Scripts\python.exe"

if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
    throw "Python Launcher was not found. Install Python 3.12 from python.org, select 'Add python.exe to PATH', then rerun this script."
}

Push-Location $Backend
try {
    if (-not (Test-Path $Python)) {
        Write-Host "Creating virtual environment with Python 3.12..." -ForegroundColor Cyan
        & py -3.12 -m venv .venv
    }

    Write-Host "Installing AEGIS dependencies..." -ForegroundColor Cyan
    & $Python -m pip install --upgrade pip
    & $Python -m pip install -r requirements.txt

    if ($SkipOcr) {
        Write-Host "OCR setup skipped. Image text extraction is disabled until Tesseract is installed or AEGIS_OCR_ENGINE is configured." -ForegroundColor Yellow
    }
    else {
        Write-Host "" 
        Write-Host "Optional OCR:" -ForegroundColor Yellow
        Write-Host "Install Tesseract for Windows and either add it to PATH or set:"
        Write-Host '  $env:AEGIS_TESSERACT_CMD = "C:\Program Files\Tesseract-OCR\tesseract.exe"'
        Write-Host "The core app works without it; image text extraction will report that OCR is unavailable."
    }

    Write-Host "" 
    Write-Host "Setup complete. Start AEGIS with:" -ForegroundColor Green
    Write-Host "  .\scripts\run-windows.ps1"
}
finally {
    Pop-Location
}
