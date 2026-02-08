@echo off
echo ========================================
echo Slideshow Configuration Builder Server
echo ========================================
echo.
echo Installing dependencies...
pip install -r requirements.txt
echo.
echo Starting server at http://localhost:5000
echo.
echo Keep this window open while using the web interface.
echo Press Ctrl+C to stop the server.
echo.
echo ========================================
python server.py
pause
