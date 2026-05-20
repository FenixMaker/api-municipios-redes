@echo off
setlocal EnableExtensions
chcp 65001 >nul 2>&1

rem Duplo clique: abre janela permanente com o log da API
if /i not "%~1"=="_run" (
  start "REDES - API IBGE" "%ComSpec%" /k call "%~f0" _run
  exit /b 0
)

title REDES - API IBGE
echo.
echo ============================================
echo   REDES - Iniciando API
echo ============================================
echo.

call "%~dp0_portable-init.bat" "%~f0"
if errorlevel 1 (
  echo.
  pause
  exit /b 1
)

echo Pasta do projeto: %ROOT%
for /f "delims=" %%V in ('"%PY%" %PYARGS% -c "import sys; print(sys.version.split()[0])" 2^>nul') do set "PYVER=%%V"
if defined PYVER echo Python do sistema: %PY% %PYARGS% ^(v%PYVER%^)
echo.

call "%~dp0_venv-setup.bat"
if errorlevel 1 (
  echo.
  pause
  exit /b 1
)
set "PYEXE=%ROOT%\.venv\Scripts\python.exe"

if not exist "%ROOT%\data" mkdir "%ROOT%\data"
if not exist "%ROOT%\data\ibge_api.db" (
  echo Gerando banco data\ibge_api.db ^(3000 registros, sem internet^)...
  "%PYEXE%" "%ROOT%\scripts\seed_db.py" --count 3000
  if errorlevel 1 (
    echo [ERRO] seed_db.py falhou.
    pause
    exit /b 1
  )
) else (
  echo Banco data\ibge_api.db ja existe - mantendo.
)

set "PORT=8000"
call :PortEmUso %PORT%
if not errorlevel 1 (
  echo.
  echo [AVISO] A porta %PORT% ja esta em uso neste PC.
  echo         Feche a outra API ^(Ctrl+C^) ou altere a porta no final deste .bat.
  echo.
)

echo.
echo ============================================
echo   API:     http://127.0.0.1:%PORT%
echo   Swagger: http://127.0.0.1:%PORT%/docs
echo   Parar:   Ctrl+C nesta janela
echo ============================================
echo.

start "" "http://127.0.0.1:%PORT%/docs"
cd /d "%ROOT%"
"%PYEXE%" -m uvicorn app.main:app --host 127.0.0.1 --port %PORT%

echo.
echo API encerrada.
pause
exit /b %ERRORLEVEL%

:PortEmUso
netstat -ano 2>nul | findstr /r /c:":%1 .*LISTENING" /c:":%1 .*LISTEN" >nul
if not errorlevel 1 exit /b 0
exit /b 1
