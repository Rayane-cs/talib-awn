#!/bin/bash
# ══════════════════════════════════════════════════════════════════════════════
#  start_server.sh  —  Talib-Awn · طالب عون
#  Server startup script with checks
# ══════════════════════════════════════════════════════════════════════════════

set -e  # Exit on error

echo "🚀 Starting Talib-Awn Backend Server"
echo "===================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed"
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install/upgrade dependencies
echo "📦 Installing dependencies..."
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt > /dev/null 2>&1
echo "✅ Dependencies installed"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "Creating default .env file..."
    cat > .env << EOF
# Database Configuration
DB_USER=root
DB_PASS=
DB_HOST=localhost
DB_NAME=talibawn

# Security
JWT_SECRET=change-me-to-secure-secret-key

# Email Configuration
GMAIL_ADDRESS=universitychlefclub@gmail.com
GMAIL_APP_PASS=

# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=True
EOF
    echo "✅ Created .env file - Please update with your credentials"
fi

# Check if database is accessible (MySQL)
echo "🔍 Checking database connection..."
if command -v mysql &> /dev/null; then
    DB_USER=$(grep DB_USER .env | cut -d '=' -f2)
    DB_HOST=$(grep DB_HOST .env | cut -d '=' -f2)
    DB_NAME=$(grep DB_NAME .env | cut -d '=' -f2)
    
    if mysql -h"${DB_HOST:-localhost}" -u"${DB_USER:-root}" -e "USE ${DB_NAME:-talibawn};" 2>/dev/null; then
        echo "✅ Database connection successful"
    else
        echo "⚠️  Warning: Cannot connect to database"
        echo "   Make sure MySQL is running and credentials in .env are correct"
    fi
else
    echo "⚠️  MySQL client not found - skipping database check"
fi

# Check port availability
if lsof -Pi :5000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Warning: Port 5000 is already in use"
    echo "   Stopping existing process..."
    kill $(lsof -t -i:5000) 2>/dev/null || true
    sleep 2
fi

echo ""
echo "===================================="
echo "🎉 All checks passed!"
echo "===================================="
echo ""
echo "Starting Flask server on http://localhost:5000"
echo "API endpoints available at http://localhost:5000/api/"
echo ""
echo "Press CTRL+C to stop the server"
echo ""

# Start the server
python3 app.py
