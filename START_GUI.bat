@echo off
echo ============================================================
echo Slideshow GUI Launcher
echo ============================================================
echo.

REM Check if we're in the right directory
if not exist "web_gui\server.py" (
    echo [ERROR] Cannot find web_gui\server.py
    echo Please run this script from the Parents directory
    pause
    exit /b 1
)

REM Run diagnostics first
echo [1/3] Running diagnostics...
python diagnose_gui.py
echo.

if errorlevel 1 (
    echo [ERROR] Diagnostic checks failed. Please fix the issues above.
    pause
    exit /b 1
)

echo [2/3] Starting Flask backend server...
echo.
echo The server will open in a new window.
echo IMPORTANT: Keep the server window open while using the GUI!
echo.

REM Start server in a new window
start "Slideshow Backend Server" cmd /k "cd web_gui && python server.py"

REM Wait a bit for server to start
timeout /t 3 /nobreak > nul

echo [3/3] Opening GUI in your default browser...
echo.

REM Open the GUI in browser
start "" "web_gui\index.html"

echo ============================================================
echo GUI launched successfully!
echo.
echo - Backend server is running in a separate window
echo - GUI should open in your browser
echo - To stop: Close the backend server window
echo ============================================================
echo.
pause
