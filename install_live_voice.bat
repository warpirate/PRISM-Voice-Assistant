@echo off
echo ========================================
echo PRISM Live Voice Installation
echo ========================================
echo.

REM Check if venv exists
if not exist "venv\" (
    echo Virtual environment not found!
    echo Please run setup.bat first to create the virtual environment.
    pause
    exit /b 1
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Upgrading google-generativeai for Live API support...
python -m pip install --upgrade google-generativeai

echo.
echo Verifying PyAudio installation...
python -c "import pyaudio; print('PyAudio version:', pyaudio.__version__)"

if errorlevel 1 (
    echo.
    echo WARNING: PyAudio not properly installed!
    echo Live Voice requires PyAudio for audio streaming.
    echo Please ensure PyAudio is installed correctly.
    echo.
    pause
)

echo.
echo ========================================
echo Installation complete!
echo ========================================
echo.
echo You can now use Live Voice mode in PRISM.
echo Click the Live Voice button (radio waves icon) to start.
echo.
pause
