@echo off
echo ========================================
echo Starting PRISM Voice Assistant
echo ========================================
echo.

REM Check if .env exists
if not exist .env (
    echo ERROR: .env file not found!
    echo Please copy .env.example to .env and add your API keys.
    pause
    exit /b 1
)

REM Check if node_modules exists
if not exist ui\node_modules (
    echo Installing Node.js dependencies...
    cd ui
    call npm install
    cd ..
)

REM Start the application
echo Starting PRISM...
cd ui
start /B npm start
cd ..

echo.
echo PRISM is starting...
echo Check the system tray for the PRISM icon.
echo.
pause
