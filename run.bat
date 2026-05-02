@echo off
REM Starter fuer den Desktop-Link
cd /d "%~dp0"

REM venv aktivieren, falls vorhanden
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

python main.py %*
echo.
echo Fertig. Fenster schliesst sich nach Tastendruck.
pause >nul
