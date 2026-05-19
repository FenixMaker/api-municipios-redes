# Inicia a API com o mesmo Python deste projeto (não exige uvicorn no PATH).
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if (Test-Path "$Root\.venv\Scripts\python.exe") {
    & "$Root\.venv\Scripts\python.exe" -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
} else {
    python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
}
