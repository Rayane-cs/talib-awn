#!/usr/bin/env python3
# ══════════════════════════════════════════════════════════════════════════════
#  test_server.py  —  Talib-Awn · طالب عون
#  Quick server test without full setup
# ══════════════════════════════════════════════════════════════════════════════

import sys
import os

print("🔍 Testing Talib-Awn Backend Setup\n")
print("=" * 60)

# Test 1: Python version
print("\n✓ Test 1: Python Version")
print(f"  Python {sys.version}")
if sys.version_info < (3, 8):
    print("  ❌ ERROR: Python 3.8+ required!")
    sys.exit(1)
print("  ✅ PASS")

# Test 2: Check if in correct directory
print("\n✓ Test 2: Project Files")
required_files = ['app.py', 'models.py', 'routes.py', 'requirements.txt']
missing = [f for f in required_files if not os.path.exists(f)]
if missing:
    print(f"  ❌ ERROR: Missing files: {', '.join(missing)}")
    print("  Make sure you're in the talib-awn directory")
    sys.exit(1)
print("  ✅ PASS - All project files found")

# Test 3: Check dependencies
print("\n✓ Test 3: Python Dependencies")
missing_deps = []
deps_to_check = [
    ('flask', 'Flask'),
    ('flask_sqlalchemy', 'Flask-SQLAlchemy'),
    ('flask_jwt_extended', 'Flask-JWT-Extended'),
    ('flask_cors', 'Flask-CORS'),
    ('pymysql', 'PyMySQL'),
    ('dotenv', 'python-dotenv'),
]

for module, package in deps_to_check:
    try:
        __import__(module)
        print(f"  ✅ {package}")
    except ImportError:
        print(f"  ❌ {package} - NOT INSTALLED")
        missing_deps.append(package)

if missing_deps:
    print(f"\n  ⚠️  Missing dependencies: {', '.join(missing_deps)}")
    print("  Install with: pip install -r requirements.txt")
    sys.exit(1)

# Test 4: Check .env file
print("\n✓ Test 4: Environment Configuration")
if not os.path.exists('.env'):
    print("  ⚠️  WARNING: .env file not found!")
    print("  Creating default .env file...")
    with open('.env', 'w') as f:
        f.write("""# Database Configuration
DB_USER=root
DB_PASS=
DB_HOST=localhost
DB_NAME=talibawn

# Security
JWT_SECRET=change-me-to-secure-random-secret

# Email Configuration
GMAIL_ADDRESS=universitychlefclub@gmail.com
GMAIL_APP_PASS=

# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=True
""")
    print("  ✅ Created .env file")
    print("  ⚠️  IMPORTANT: Update DB_PASS and GMAIL_APP_PASS in .env")
else:
    print("  ✅ .env file exists")

# Test 5: Check database connection
print("\n✓ Test 5: Database Connection")
try:
    import pymysql
    from dotenv import load_dotenv
    load_dotenv()
    
    db_user = os.getenv('DB_USER', 'root')
    db_pass = os.getenv('DB_PASS', '')
    db_host = os.getenv('DB_HOST', 'localhost')
    db_name = os.getenv('DB_NAME', 'talibawn')
    
    print(f"  Connecting to: {db_user}@{db_host}/{db_name}")
    
    # Try to connect
    conn = pymysql.connect(
        host=db_host,
        user=db_user,
        password=db_pass,
        connect_timeout=5
    )
    
    cursor = conn.cursor()
    
    # Check if database exists
    cursor.execute(f"SHOW DATABASES LIKE '{db_name}'")
    if not cursor.fetchone():
        print(f"  ⚠️  Database '{db_name}' does not exist")
        print(f"  Creating database...")
        cursor.execute(f"CREATE DATABASE {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        print(f"  ✅ Database '{db_name}' created")
    else:
        print(f"  ✅ Database '{db_name}' exists")
    
    conn.close()
    print("  ✅ Database connection successful")
    
except Exception as e:
    print(f"  ❌ ERROR: {e}")
    print("  Make sure MySQL is running:")
    print("    - Linux: sudo systemctl start mysql")
    print("    - macOS: brew services start mysql")
    print("    - Windows: net start MySQL")
    sys.exit(1)

# Test 6: Try to import app
print("\n✓ Test 6: Flask Application")
try:
    from app import create_app
    app = create_app()
    print("  ✅ Flask app created successfully")
except Exception as e:
    print(f"  ❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 7: Check port availability
print("\n✓ Test 7: Port Availability")
import socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
result = sock.connect_ex(('localhost', 5000))
sock.close()

if result == 0:
    print("  ⚠️  WARNING: Port 5000 is already in use")
    print("  Stop the existing server or change the port in app.py")
else:
    print("  ✅ Port 5000 is available")

# Summary
print("\n" + "=" * 60)
print("✅ ALL TESTS PASSED!")
print("=" * 60)
print("\n🚀 Ready to start server!")
print("\nRun the server:")
print("  python app.py")
print("\nOr use the startup script:")
print("  ./start_server.sh     (Linux/macOS)")
print("  start_server.bat      (Windows)")
print("\nServer will be available at:")
print("  http://localhost:5000/api/")
print("\n" + "=" * 60)
