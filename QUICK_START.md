# Quick Start Guide
**Talib-Awn · طالب عون**

Get the backend server running in 5 minutes!

---

## 🚀 For the Impatient

### Linux/macOS
```bash
./start_server.sh
```

### Windows
```bash
start_server.bat
```

That's it! Server will be running at http://localhost:5000

---

## 📋 Prerequisites

### Required
- ✅ Python 3.8 or higher
- ✅ MySQL 5.7 or higher
- ✅ pip (Python package manager)

### Check if you have them
```bash
python --version    # Should show Python 3.8+
mysql --version     # Should show MySQL 5.7+
pip --version       # Should show pip 20.0+
```

### Install if missing
- **Python**: [python.org/downloads](https://www.python.org/downloads/)
- **MySQL**: [dev.mysql.com/downloads](https://dev.mysql.com/downloads/installer/)

---

## ⚡ Setup Steps

### 1. Clone Repository (if not done)
```bash
git clone https://github.com/Rayane-cs/talib-awn.git
cd talib-awn
```

### 2. Create Database
```bash
# Login to MySQL
mysql -u root -p

# Create database
CREATE DATABASE talibawn CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
EXIT;
```

### 3. Configure Environment
Create `.env` file:
```bash
# Copy example
cp .env.example .env  # If exists

# OR create manually
cat > .env << EOF
DB_USER=root
DB_PASS=your_mysql_password
DB_HOST=localhost
DB_NAME=talibawn
JWT_SECRET=$(openssl rand -base64 32)
GMAIL_ADDRESS=your-email@gmail.com
GMAIL_APP_PASS=your-app-password
EOF
```

**Important:** Update with your actual credentials!

### 4. Install Dependencies
```bash
# Using pip
pip install -r requirements.txt

# OR using virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/macOS
# OR
venv\Scripts\activate     # Windows

pip install -r requirements.txt
```

### 5. Start Server

**Option A: Using startup script (recommended)**
```bash
./start_server.sh        # Linux/macOS
start_server.bat         # Windows
```

**Option B: Direct**
```bash
python app.py
```

**Option C: Production**
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### 6. Verify Installation
Open browser and visit:
- Health check: http://localhost:5000/api/
- Stats: http://localhost:5000/api/stats

Or use curl:
```bash
curl http://localhost:5000/api/
# Should return: {"ok": true, "message": "Talib-Awn API is running 🚀"}
```

---

## 🎯 Frontend Connection

### Update Frontend API URL
In your `api.js` file:
```javascript
// Change from:
const API_URL = 'http://127.0.0.1:5000/api';

// To:
const API_URL = 'http://localhost:5000/api';
```

### Start Frontend
```bash
# Using Live Server (VS Code)
# Right-click index.html → Open with Live Server

# OR using Python
python -m http.server 5501

# OR using Node.js
npx serve .
```

### Test Login
1. Open http://localhost:5501/login.html
2. Try logging in
3. Check browser console (F12) for errors

---

## 🔧 Common Issues

### Port 5000 Already in Use
```bash
# Find process using port 5000
lsof -i :5000              # macOS/Linux
netstat -ano | findstr 5000  # Windows

# Kill it
kill -9 <PID>              # macOS/Linux
taskkill /PID <PID> /F     # Windows
```

### MySQL Connection Failed
```bash
# Check if MySQL is running
sudo systemctl status mysql  # Linux
brew services list           # macOS
net start                    # Windows

# Start MySQL if stopped
sudo systemctl start mysql   # Linux
brew services start mysql    # macOS
net start MySQL              # Windows
```

### CORS Errors
1. Verify backend is running: `curl http://localhost:5000/api/`
2. Check frontend uses correct URL (localhost, not 127.0.0.1)
3. Restart both frontend and backend servers

### Module Not Found
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# OR activate virtual environment first
source venv/bin/activate
pip install -r requirements.txt
```

**For more issues, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md)**

---

## 📚 Next Steps

### Testing
```bash
# Test registration
curl -X POST http://localhost:5000/api/auth/register/send-otp \
  -H "Content-Type: application/json" \
  -d '{
    "email":"test@test.com",
    "password":"Test1234",
    "firstname":"Test",
    "lastname":"User",
    "type":"student"
  }'

# Test login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"Test1234"}'
```

### Create Admin User
```bash
# Open MySQL
mysql -u root -p talibawn

# Update user to admin
UPDATE users SET type='admin' WHERE email='your-email@test.com';
EXIT;
```

### Development
- Read [BACKEND_IMPROVEMENTS.md](BACKEND_IMPROVEMENTS.md) for architecture
- Check [DATABASE.md](DATABASE.md) for schema
- Review [SECURITY.md](SECURITY.md) for security practices

---

## 🎓 API Endpoints

### Authentication
- `POST /api/auth/register/send-otp` - Send registration OTP
- `POST /api/auth/register/verify-otp` - Complete registration
- `POST /api/auth/login` - Login with email/password
- `POST /api/auth/login/send-otp` - Passwordless login OTP
- `POST /api/auth/login/verify-otp` - Verify login OTP
- `GET /api/auth/me` - Get current user
- `POST /api/auth/refresh` - Refresh access token

### Users
- `GET /api/users/<id>` - Get user profile
- `PATCH /api/users/me` - Update profile
- `GET /api/users/search?q=name` - Search users

### Projects
- `GET /api/projects` - List projects
- `POST /api/projects` - Create project
- `PATCH /api/projects/<id>` - Update project
- `DELETE /api/projects/<id>` - Delete project
- `POST /api/projects/<id>/like` - Like/unlike project

### Events
- `GET /api/events` - List events
- `POST /api/events/<id>/register` - Register for event

### More endpoints in documentation

---

## ✅ Quick Checklist

Before asking for help:

- [ ] Python 3.8+ installed
- [ ] MySQL running and accessible
- [ ] Database `talibawn` created
- [ ] `.env` file configured
- [ ] Dependencies installed (`pip list`)
- [ ] Port 5000 available
- [ ] Server starts without errors
- [ ] Health check returns OK
- [ ] Frontend uses correct API URL
- [ ] Browser console shows no CORS errors

---

## 🆘 Need Help?

1. **Check logs**: Terminal output or `server.log`
2. **Read troubleshooting**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
3. **Test with curl**: Verify API directly
4. **Check documentation**: See other MD files
5. **GitHub issues**: Open an issue with error details

---

## 🎉 Success!

If you see:
```
✅  Database tables ready.
🚀  Starting Talib-Awn API on http://localhost:5000
```

You're all set! Happy coding! 🚀

---

**Quick Links:**
- [Backend Improvements](BACKEND_IMPROVEMENTS.md)
- [Database Schema](DATABASE.md)
- [Security Guide](SECURITY.md)
- [Troubleshooting](TROUBLESHOOTING.md)
