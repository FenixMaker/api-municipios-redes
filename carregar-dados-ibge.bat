@echo off
setlocal EnableExtensions
chcp 65001 >nul 2>&1

echo.
echo ============================================
echo   REDES - Carga oficial IBGE
echo ============================================
echo   Requer INTERNET. Pode levar alguns minutos.
echo ============================================
echo.

call "%~dp0_portable-init.bat" "%~f0"
if errorlevel 1 (
  pause
  exit /b 1
)

call "%~dp0_venv-setup.bat"
if errorlevel 1 (
  pause
  exit /b 1
)
set "PYEXE=%ROOT%\.venv\Scripts\python.exe"

if not exist "%ROOT%\data" mkdir "%ROOT%\data"

cd /d "%ROOT%"
"%PYEXE%" "%ROOT%\scripts\load_ibge_municipios.py" %*
set "RC=%ERRORLEVEL%"
echo.
if not "%RC%"=="0" (
  echo Carga finalizou com codigo %RC%.
) else (
  echo Carga concluida. Banco em data\ibge_api.db
)
pause
exit /b %RC%
