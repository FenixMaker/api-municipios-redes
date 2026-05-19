@echo off
rem Duplo clique: abre janela que permanece aberta e mostra cada etapa
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
echo.

call "%~dp0_venv-setup.bat"
if errorlevel 1 (
  echo.
  pause
  popd >nul 2>&1
  exit /b 1
)
set "PYEXE=%ROOT%\.venv\Scripts\python.exe"

if not exist "%ROOT%\data\ibge_api.db" (
  echo Gerando banco data\ibge_api.db ^(3000 registros, sem internet^)...
  if not exist "%ROOT%\data" mkdir "%ROOT%\data"
  "%PYEXE%" "%ROOT%\scripts\seed_db.py" --count 3000
  if errorlevel 1 (
    echo [ERRO] seed_db.py falhou.
    pause
    popd >nul 2>&1
    exit /b 1
  )
) else (
  echo Banco data\ibge_api.db ja existe - mantendo.
)

echo.
echo ============================================
echo   API:     http://127.0.0.1:8000
echo   Swagger: http://127.0.0.1:8000/docs
echo   Parar:   Ctrl+C nesta janela
echo ============================================
echo.

start "" "http://127.0.0.1:8000/docs"
rem Sem --reload: evita monitorar .venv e trava em venv corrompido
"%PYEXE%" -m uvicorn app.main:app --host 127.0.0.1 --port 8000

echo.
echo API encerrada.
pause
popd >nul 2>&1
exit /b %ERRORLEVEL%
