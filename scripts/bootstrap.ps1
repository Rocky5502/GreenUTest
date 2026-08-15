$ErrorActionPreference = "Stop"

if (-not (Test-Path ".venv")) {
    py -3.11 -m venv .venv
}

& .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
python -m greenutest doctor
python -m greenutest dry-run --output artifacts/dry-run
python -m unittest discover -s tests -v
Write-Host "GreenUTest dry-run setup passed. No model download or benchmark execution was performed." -ForegroundColor Green
