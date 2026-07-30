@echo off
echo Instalace chybejicich knihoven pro IBT Journal...
python -m pip install openpyxl matplotlib --quiet
if %errorlevel% == 0 (
    echo.
    echo Hotovo! Restartuj program.
) else (
    echo.
    echo Chyba instalace. Zkus spustit jako Administrator.
)
pause
