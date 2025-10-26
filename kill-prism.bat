@echo off
REM Kill all PRISM processes

echo ====================================
echo  Stopping PRISM Processes
echo ====================================
echo.

echo Killing Python backend processes...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq PRISM Backend*" 2>nul
taskkill /F /IM python.exe /FI "COMMANDLINE eq *backend\main.py*" 2>nul

echo.
echo Killing Electron UI processes...
taskkill /F /IM electron.exe /FI "WINDOWTITLE eq PRISM*" 2>nul

echo.
echo Checking for processes using port 9876...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :9876') do (
    echo Killing process using port 9876: %%a
    taskkill /F /PID %%a 2>nul
)

echo.
echo ====================================
echo  All PRISM processes stopped
echo ====================================
echo.
echo You can now run start.bat
echo.
pause
