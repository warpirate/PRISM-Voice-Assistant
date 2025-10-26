@echo off
REM Python 3.12 Compatibility Fix
REM Fixes distutils and other Python 3.12 issues

echo ====================================
echo  Python 3.12 Compatibility Fix
echo ====================================
echo.

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo.

REM Install setuptools (provides distutils for Python 3.12)
echo Installing setuptools for distutils compatibility...
pip install --upgrade setuptools==69.0.0
echo.

REM Update SpeechRecognition for Python 3.12
echo Updating SpeechRecognition...
pip install --upgrade SpeechRecognition==3.10.4
echo.

REM Install numpy if missing
echo Ensuring numpy is installed...
pip install numpy==1.26.4
echo.

REM Reinstall all dependencies
echo Reinstalling all dependencies...
pip install --upgrade -r requirements.txt
echo.

echo ====================================
echo  Python 3.12 Fixes Applied!
echo ====================================
echo.
echo You can now run start.bat
echo.
pause
