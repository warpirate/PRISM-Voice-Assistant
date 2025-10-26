@echo off
echo ========================================
echo PRISM Setup Script
echo ========================================
echo.

echo Step 1: Installing Python dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install Python dependencies
    pause
    exit /b 1
)

echo.
echo Step 2: Installing Node.js dependencies...
cd ui
call npm install
if errorlevel 1 (
    echo ERROR: Failed to install Node.js dependencies
    cd ..
    pause
    exit /b 1
)
cd ..

echo.
echo Step 3: Creating .env file...
if not exist .env (
    copy .env.example .env
    echo .env file created. Please edit it and add your API keys.
) else (
    echo .env file already exists.
)

echo.
echo Step 4: Creating directories...
if not exist logs mkdir logs
if not exist temp mkdir temp
if not exist ui\assets mkdir ui\assets

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Edit .env file and add your API keys:
echo    - NEBIUS_API_KEY (required)
echo    - PORCUPINE_ACCESS_KEY (optional, for wake word)
echo.
echo 2. Run start.bat to launch PRISM
echo.
pause
