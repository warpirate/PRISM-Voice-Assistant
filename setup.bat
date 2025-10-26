@echo off
REM PRISM Setup Script

echo ====================================
echo  PRISM Setup
echo ====================================
echo.

REM Check Python
echo Checking for Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH.
    echo Please install Python 3.8 or higher from python.org
    pause
    exit /b 1
)

python --version
echo.

REM Check Node.js
echo Checking for Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js is not installed or not in PATH.
    echo Please install Node.js from nodejs.org
    pause
    exit /b 1
)

node --version
echo.

REM Create virtual environment
if not exist "venv\" (
    echo Creating Python virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo Virtual environment created.
) else (
    echo Virtual environment already exists.
)
echo.

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo.

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip
echo.

REM Install Python dependencies
echo Installing Python dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo WARNING: Some Python packages may have failed to install.
    echo PyAudio installation often requires additional setup on Windows.
    echo.
    echo To install PyAudio:
    echo 1. Download the wheel file for your Python version from:
    echo    https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
    echo 2. Install it with: pip install PyAudio-X.X.X-cpXX-cpXX-win_amd64.whl
    echo.
    pause
)
echo.

REM Install Node dependencies
echo Installing Node.js dependencies...
if not exist "package.json" (
    echo ERROR: package.json not found in root directory.
    pause
    exit /b 1
)

call npm install
if errorlevel 1 (
    echo ERROR: Failed to install Node dependencies.
    pause
    exit /b 1
)
echo.

REM Create data directory
if not exist "data\" (
    echo Creating data directory...
    mkdir data
    mkdir data\logs
)

REM Create assets directory
if not exist "ui\assets\" (
    echo Creating assets directory...
    mkdir ui\assets
    echo NOTE: Add icon.png and tray-icon.png to ui\assets\ for custom icons.
    echo See ui\assets\README.md for details.
    echo.
)

REM Create .env from example if it doesn't exist
if not exist ".env" (
    echo Creating .env file from .env.example...
    copy .env.example .env
    echo.
    echo IMPORTANT: Please edit .env and add your API keys!
    echo.
)

echo ====================================
echo  Setup Complete!
echo ====================================
echo.
echo Next steps:
echo 1. Edit .env file and add your API keys
echo 2. Run start.bat to launch PRISM
echo.
pause
