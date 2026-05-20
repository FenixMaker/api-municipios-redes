@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "ROOT="
set "PY="
set "PYARGS="

if not "%~1"=="" (
  for %%I in ("%~1") do set "ROOT=%%~dpI"
) else (
  set "ROOT=%~dp0"
)
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

cd /d "%ROOT%" 2>nul
if errorlevel 1 (
  echo [ERRO] Nao foi possivel acessar a pasta do projeto:
  echo   %ROOT%
  exit /b 1
)
set "ROOT=%CD%"

call :FindPython
if errorlevel 1 exit /b 1

endlocal & set "ROOT=%ROOT%" & set "PY=%PY%" & set "PYARGS=%PYARGS%"
exit /b 0

:FindPython
set "PY="
set "PYARGS="

rem 1) Launcher py (Windows) — versoes 3.10 a 3.13
where py >nul 2>&1
if not errorlevel 1 (
  for %%V in (-3.13 -3.12 -3.11 -3.10 -3) do (
    if not defined PY (
      call :TryPython "py" "%%V"
    )
  )
)

rem 2) Pastas Python3xx em AppData / Program Files (qualquer versao instalada)
if exist "%LOCALAPPDATA%\Programs\Python\" (
  for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python*") do (
    if not defined PY if exist "%%~D\python.exe" call :TryPython "%%~D\python.exe" ""
  )
)
for %%B in ("%ProgramFiles%" "%ProgramFiles(x86)%") do (
  if exist "%%~B\Python*" (
    for /d %%D in ("%%~B\Python*") do (
      if not defined PY if exist "%%~D\python.exe" call :TryPython "%%~D\python.exe" ""
    )
  )
)

rem 3) Registro do Windows (instalador python.org)
if not defined PY (
  for %%R in (
    "HKLM\SOFTWARE\Python\PythonCore"
    "HKCU\SOFTWARE\Python\PythonCore"
    "HKLM\SOFTWARE\WOW6432Node\Python\PythonCore"
  ) do (
    for /f "tokens=2,*" %%A in ('reg query %%R /s /v ExecutablePath 2^>nul ^| findstr /i ExecutablePath') do (
      if not defined PY (
        set "REGPY=%%B"
        if defined REGPY call :TryPython "!REGPY!" ""
      )
    )
  )
)

rem 4) python / python3 no PATH (ignora atalhos da Microsoft Store)
if not defined PY (
  for %%P in (python python3) do (
    where %%P >nul 2>&1
    if not errorlevel 1 (
      for /f "delims=" %%F in ('where %%P 2^>nul') do (
        if not defined PY (
          echo %%F | findstr /i /c:"WindowsApps" /c:"Microsoft\\WindowsApps" >nul
          if errorlevel 1 call :TryPython "%%F" ""
        )
      )
    )
  )
)

if not defined PY goto :FindPython_fail

exit /b 0

:TryPython
set "CAND=%~1"
set "ARGS=%~2"
if /i "%CAND%"=="py" (
  %CAND% %ARGS% -c "import sys; v=sys.version_info; raise SystemExit(0 if v.major==3 and v.minor>=10 else 1)" >nul 2>&1
) else (
  "%CAND%" -c "import sys; v=sys.version_info; raise SystemExit(0 if v.major==3 and v.minor>=10 else 1)" >nul 2>&1
)
if errorlevel 1 exit /b 1
if /i "%CAND%"=="py" (
  set "PY=py"
  set "PYARGS=%ARGS%"
) else (
  set "PY=%CAND%"
  set "PYARGS="
)
exit /b 0

:FindPython_fail
echo.
echo [ERRO] Python 3.10+ nao encontrado neste PC.
echo.
echo   Instale em https://www.python.org/downloads/
echo   Marque "Add python.exe to PATH" e reinicie o terminal.
echo   Ou instale o "Python Launcher" ^(comando py^).
echo.
exit /b 1
