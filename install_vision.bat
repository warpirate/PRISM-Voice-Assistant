@echo off
echo ============================================================
echo PRISM Vision Agent Installation
echo ============================================================
echo.
echo Installing computer vision dependencies...
echo.

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install vision dependencies
pip install Pillow>=10.0.0
pip install mss>=9.0.0
pip install opencv-python>=4.8.0

echo.
echo ============================================================
echo Installation Complete!
echo ============================================================
echo.
echo Vision Agent is now ready to use.
echo.
echo Next steps:
echo 1. Restart PRISM: npm start
echo 2. Try: "send message to [contact] on WhatsApp"
echo 3. PRISM will now use computer vision to understand UI
echo.
pause
