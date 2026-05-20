@echo off
setlocal EnableExtensions EnableDelayedExpansion

if not defined ROOT (
  echo [ERRO] _venv-setup.bat exige ROOT ^(execute _portable-init.bat antes^).
  exit /b 1
)
if not defined PY (
  echo [ERRO] _venv-setup.bat exige PY ^(execute _portable-init.bat antes^).
  exit /b 1
)

set "PYEXE=%ROOT%\.venv\Scripts\python.exe"

if not exist "%ROOT%\requirements.txt" (
  echo [ERRO] requirements.txt nao encontrado em:
  echo   %ROOT%
  exit /b 1
)

call :VenvUsable
if not errorlevel 1 (
  echo Dependencias OK ^(.venv deste PC^).
  endlocal & set "PYEXE=%PYEXE%"
  exit /b 0
)

if exist "%ROOT%\.venv" (
  echo [AVISO] .venv ausente, corrompido ou de outro computador — recriando...
  rmdir /s /q "%ROOT%\.venv" 2>nul
  ping 127.0.0.1 -n 2 >nul
)

echo [1/2] Criando ambiente virtual .venv ...
"%PY%" %PYARGS% -m venv "%ROOT%\.venv"
if errorlevel 1 (
  echo [ERRO] Falha ao criar .venv. Verifique se o Python esta instalado corretamente.
  exit /b 1
)
set "PYEXE=%ROOT%\.venv\Scripts\python.exe"

echo [2/2] Instalando dependencias ^(1-3 min na 1a vez, aguarde^)...
"%PYEXE%" -m pip install --upgrade pip -q
if errorlevel 1 (
  echo [ERRO] pip upgrade falhou.
  exit /b 1
)
"%PYEXE%" -m pip install -r "%ROOT%\requirements.txt"
if errorlevel 1 (
  echo [ERRO] pip install falhou.
  exit /b 1
)

call :VenvUsable
if errorlevel 1 (
  echo [ERRO] Dependencias instaladas mas a API nao importa. Apague a pasta .venv e tente de novo.
  exit /b 1
)

echo Dependencias instaladas com sucesso.
endlocal & set "PYEXE=%PYEXE%"
exit /b 0

:VenvUsable
if not exist "%PYEXE%" exit /b 1

cd /d "%ROOT%"

rem Teste real: venv de outro PC ou Python removido falha aqui
"%PYEXE%" -c "import sys; import uvicorn; import fastapi; import sqlalchemy; import httpx" >nul 2>&1
if errorlevel 1 exit /b 1

"%PYEXE%" -c "from app.main import app" >nul 2>&1
if errorlevel 1 exit /b 1
exit /b 0
