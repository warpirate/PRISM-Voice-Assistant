@echo off
echo ====================================
echo  PRISM Startup with Health Check
echo ====================================
echo.

REM Activate virtual environment
call venv\Scripts\activate.bat

echo Running health checks...
echo.

REM Run dependency test
python test_realtime.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ====================================
    echo  Health Check Failed!
    echo ====================================
    echo.
    echo Please fix the issues above before starting PRISM.
    echo Run setup.bat if dependencies are missing.
    echo.
    pause
    exit /b 1
)

echo.
echo ====================================
echo  All Checks Passed!
echo ====================================
echo.
echo Starting PRISM...
echo.

REM Start PRISM
call start.bat
