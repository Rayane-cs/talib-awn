@echo off
REM ══════════════════════════════════════════════════════════════════════════════
REM  start_server.bat  —  Talib-Awn · طالب عون
REM  Windows server startup script
REM ══════════════════════════════════════════════════════════════════════════════

echo.
echo ========================================
echo 🚀 Starting Talib-Awn Backend Server
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from python.org
    pause
    exit /b 1
)

echo ✅ Python found: 
python --version

REM Check if virtual environment exists
if not exist "venv\" (
    echo 📦 Creating virtual environment...
    python -m venv venv
    echo ✅ Virtual environment created
)

REM Activate virtual environment
echo 🔄 Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/upgrade dependencies
echo 📦 Installing dependencies...
python -m pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt >nul 2>&1
echo ✅ Dependencies installed

REM Check if .env file exists
if not exist ".env" (
    echo ⚠️  Warning: .env file not found!
    echo Creating default .env file...
    (
        echo # Database Configuration
        echo DB_USER=root
        echo DB_PASS=
        echo DB_HOST=localhost
        echo DB_NAME=talibawn
        echo.
        echo # Security
        echo JWT_SECRET=change-me-to-secure-secret-key
        echo.
        echo # Email Configuration
        echo GMAIL_ADDRESS=universitychlefclub@gmail.com
        echo GMAIL_APP_PASS=
        echo.
        echo # Flask Configuration
        echo FLASK_ENV=development
        echo FLASK_DEBUG=True
    ) > .env
    echo ✅ Created .env file - Please update with your credentials
)

REM Check if port 5000 is in use
netstat -an | findstr ":5000" >nul 2>&1
if not errorlevel 1 (
    echo ⚠️  Warning: Port 5000 is already in use
    echo Please close the application using port 5000 or change the port in app.py
    pause
)

echo.
echo ========================================
echo 🎉 Starting server...
echo ========================================
echo.
echo Server will be available at: http://localhost:5000
echo API endpoints at: http://localhost:5000/api/
echo.
echo Press CTRL+C to stop the server
echo.

REM Start the server
python app.py

pause
