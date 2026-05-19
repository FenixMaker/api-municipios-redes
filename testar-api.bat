@echo off
setlocal EnableExtensions
chcp 65001 >nul 2>&1

if /i "%~1"=="nopause" set "NOPAUSE=1"

call "%~dp0_portable-init.bat" "%~f0"
if errorlevel 1 (
  if not defined NOPAUSE pause
  exit /b 1
)

echo Pasta do projeto: %ROOT%
echo.

call "%~dp0_venv-setup.bat"
if errorlevel 1 (
  if not defined NOPAUSE pause
  popd >nul 2>&1
  exit /b 1
)
set "PYEXE=%ROOT%\.venv\Scripts\python.exe"

echo Executando pytest com "%PYEXE%" ...
"%PYEXE%" -m pytest "%ROOT%\tests" -v --tb=short
set "RC=%ERRORLEVEL%"
echo.
if not "%RC%"=="0" (
  echo Testes finalizaram com codigo %RC%.
) else (
  echo Todos os testes passaram.
)
popd >nul 2>&1
if defined NOPAUSE exit /b %RC%
pause
exit /b %RC%
