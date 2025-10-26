@echo off
REM PRISM Startup Script

echo ====================================
echo  Starting PRISM
echo ====================================

REM Check if virtual environment exists
if not exist "venv\" (
    echo Virtual environment not found. Running setup...
    call setup.bat
    if errorlevel 1 (
        echo Setup failed. Please check the errors above.
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if .env exists
if not exist ".env" (
    echo.
    echo WARNING: .env file not found!
    echo Please copy .env.example to .env and configure your API keys.
    echo.
    pause
    exit /b 1
)

REM Start backend
echo Starting PRISM backend...
start "PRISM Backend" cmd /k "venv\Scripts\activate.bat && python backend\main.py"

REM Wait a moment for backend to start
timeout /t 3 /nobreak >nul

REM Start Electron UI
echo Starting PRISM UI...
cd ui
start "PRISM UI" cmd /k "npm start"

echo.
echo ====================================
echo  PRISM Started Successfully!
echo ====================================
echo.
echo Backend and UI are running in separate windows.
echo Close those windows to stop PRISM.
echo.
pause
