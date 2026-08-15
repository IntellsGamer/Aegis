<#
.SYNOPSIS
    Start AEGIS on native Windows after setup-windows.ps1 has completed.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\scripts\run-windows.ps1
#>
[CmdletBinding()]
param(
    [switch]$Production,
    [switch]$DevelopmentServer
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$Backend = Join-Path $RepoRoot "backend"
$Python = Join-Path $Backend ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    throw "Windows environment is not initialized. Run .\scripts\setup-windows.ps1 first."
}

if ($Production -and $DevelopmentServer) {
    throw "Use either -Production or -DevelopmentServer, not both."
}
if ($Production) {
    $env:AEGIS_ENVIRONMENT = "production"
    if (-not $env:AEGIS_SECRET_KEY -or $env:AEGIS_SECRET_KEY -eq "change-me-in-production-please-use-a-long-random-string") {
        throw "Set a unique AEGIS_SECRET_KEY before using -Production."
    }
}
else {
    $env:AEGIS_ENVIRONMENT = "development"
}

# Waitress is the default on every native platform. Flask is available only
# when explicitly requested for local framework debugging.
$env:AEGIS_SERVER = if ($DevelopmentServer) { "flask" } else { "waitress" }

Push-Location $Backend
try {
    & $Python run.py
}
finally {
    Pop-Location
}
