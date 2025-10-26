@echo off
REM PRISM Fix Script
REM Fixes common installation issues

echo ====================================
echo  PRISM Fix Script
echo ====================================
echo.

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo.

REM Fix 1: Install missing Python dependencies
echo Installing missing Python dependencies...
pip install setuptools==69.0.0 numpy==1.26.4 SpeechRecognition==3.10.4
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo.

REM Fix 2: Reinstall Electron
echo Fixing Electron installation...
echo Removing corrupted Electron...
rmdir /s /q node_modules\electron 2>nul
echo.

echo Reinstalling Electron...
call npm install electron@^28.2.0
if errorlevel 1 (
    echo ERROR: Failed to reinstall Electron
    pause
    exit /b 1
)
echo.

echo ====================================
echo  Fixes Applied Successfully!
echo ====================================
echo.
echo You can now run start.bat to launch PRISM
echo.
pause
