<#
.SYNOPSIS
    Prepare a native Windows development environment for AEGIS.

.DESCRIPTION
    Requires the Python launcher with Python 3.12 and Node.js 20+ installed.
    The script creates backend\.venv, installs the platform-appropriate Python
    package set, installs pinned local frontend dependencies, and builds the
    static Tailwind and Turbo assets. OCR remains optional: URL, text, email,
    QR, file, and report workflows operate without a Tesseract system installation.

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
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    throw "Node.js 20+ was not found. Install the Node.js LTS release, reopen PowerShell, then rerun this script."
}
if (-not (Get-Command corepack -ErrorAction SilentlyContinue)) {
    throw "Corepack was not found with Node.js. Install a current Node.js LTS release, reopen PowerShell, then rerun this script."
}

Push-Location $RepoRoot
try {
    Write-Host "Installing local frontend dependencies..." -ForegroundColor Cyan
    & corepack pnpm install --frozen-lockfile
    Write-Host "Building local Tailwind and Turbo assets..." -ForegroundColor Cyan
    & corepack pnpm run build:assets
}
finally {
    Pop-Location
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
