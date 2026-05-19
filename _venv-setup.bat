@echo off
set "PYEXE=%ROOT%\.venv\Scripts\python.exe"

if not exist "%ROOT%\requirements.txt" (
  echo [ERRO] requirements.txt nao encontrado em:
  echo   %ROOT%
  exit /b 1
)

call :VenvReady
if not errorlevel 1 (
  echo Dependencias OK - pulando pip install.
  exit /b 0
)

if exist "%PYEXE%" (
  echo [AVISO] .venv incompleto ou corrompido - recriando...
  rmdir /s /q "%ROOT%\.venv" 2>nul
)

echo [1/2] Criando ambiente virtual .venv ...
"%PY%" %PYARGS% -m venv "%ROOT%\.venv"
if errorlevel 1 (
  echo [ERRO] Falha ao criar .venv
  exit /b 1
)
set "PYEXE=%ROOT%\.venv\Scripts\python.exe"

echo [2/2] Instalando dependencias ^(1-3 min na 1a vez, aguarde^)...
"%PYEXE%" -m pip install --upgrade pip
if errorlevel 1 (
  echo [ERRO] pip upgrade falhou.
  exit /b 1
)
"%PYEXE%" -m pip install -r "%ROOT%\requirements.txt"
if errorlevel 1 (
  echo [ERRO] pip install falhou.
  exit /b 1
)

call :VenvReady
if errorlevel 1 (
  echo [ERRO] Dependencias instaladas mas import falhou. Apague a pasta .venv e tente de novo.
  exit /b 1
)
echo Dependencias instaladas com sucesso.
exit /b 0

:VenvReady
if not exist "%PYEXE%" exit /b 1
"%PYEXE%" -c "import sys; import uvicorn; import fastapi; import sqlalchemy; import httpx; import websockets" >nul 2>&1
if errorlevel 1 exit /b 1
"%PYEXE%" -c "from app.main import app" >nul 2>&1
if errorlevel 1 exit /b 1
exit /b 0
