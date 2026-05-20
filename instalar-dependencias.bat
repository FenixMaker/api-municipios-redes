@echo off
setlocal EnableExtensions
chcp 65001 >nul 2>&1

echo.
echo ============================================
echo   REDES - Instalar dependencias
echo ============================================
echo.

call "%~dp0_portable-init.bat" "%~f0"
if errorlevel 1 (
  pause
  exit /b 1
)

echo Pasta do projeto: %ROOT%
echo.

rem Forca recriacao do .venv (util ao copiar o projeto para outro PC)
if exist "%ROOT%\.venv" (
  echo Removendo .venv antigo...
  rmdir /s /q "%ROOT%\.venv" 2>nul
  timeout /t 1 /nobreak >nul
)

call "%~dp0_venv-setup.bat"
if errorlevel 1 (
  pause
  exit /b 1
)

echo.
echo Pronto. Use iniciar-api.bat para subir a API.
echo.
pause
exit /b 0
