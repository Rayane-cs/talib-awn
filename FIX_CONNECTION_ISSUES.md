# Fix Connection Issues - تصليح مشاكل الاتصال
**Talib-Awn · طالب عون**

---

## ❌ Problem / المشكلة

**Error Message:**
```
تعذّر الاتصال بالخادم
(Unable to connect to server)
```

**Causes / الأسباب:**
1. ❌ Backend server not running / الخادم غير مشغل
2. ❌ Dependencies not installed / المكتبات غير مثبتة
3. ❌ Database not configured / قاعدة البيانات غير مهيأة
4. ❌ Wrong API URL / عنوان API خاطئ

---

## ✅ Solution / الحل

### Step 1: Install Python Dependencies / تثبيت المكتبات

```bash
# Navigate to project directory / انتقل إلى مجلد المشروع
cd talib-awn

# Install dependencies / ثبت المكتبات
pip install -r requirements.txt
```

**Expected Output:**
```
Successfully installed flask-2.3.0 flask-sqlalchemy-3.0.0 ...
```

If you get errors, try:
```bash
# Use pip3 instead
pip3 install -r requirements.txt

# OR with sudo (Linux/macOS)
sudo pip3 install -r requirements.txt

# OR in virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

---

### Step 2: Setup Database / إعداد قاعدة البيانات

#### 2.1: Start MySQL / شغل MySQL

**Linux:**
```bash
sudo systemctl start mysql
sudo systemctl status mysql  # Check status
```

**macOS:**
```bash
brew services start mysql
brew services list  # Check status
```

**Windows:**
```cmd
net start MySQL
```

#### 2.2: Create Database / أنشئ قاعدة البيانات

```bash
# Login to MySQL / سجل دخول
mysql -u root -p

# Create database / أنشئ القاعدة
CREATE DATABASE talibawn CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# Verify / تحقق
SHOW DATABASES;

# Exit / خروج
EXIT;
```

---

### Step 3: Configure Environment / إعداد البيئة

#### 3.1: Create .env file / أنشئ ملف .env

```bash
# Copy example file / انسخ الملف المثال
cp .env.example .env

# OR create manually / أو أنشئه يدوياً
cat > .env << EOF
DB_USER=root
DB_PASS=your_mysql_password_here
DB_HOST=localhost
DB_NAME=talibawn
JWT_SECRET=change-me-to-secure-random-secret
GMAIL_ADDRESS=universitychlefclub@gmail.com
GMAIL_APP_PASS=your-app-password
EOF
```

#### 3.2: Update .env with your credentials / حدّث ملف .env ببياناتك

**Important fields to update:**
- `DB_PASS` - Your MySQL password / كلمة مرور MySQL
- `GMAIL_APP_PASS` - Google App Password / كلمة مرور تطبيق Google

**How to get Google App Password:**
1. Go to: https://myaccount.google.com/security
2. Enable 2-Step Verification / فعّل التحقق بخطوتين
3. App passwords → Generate / كلمات مرور التطبيقات → إنشاء
4. Copy the 16-character password / انسخ كلمة المرور

---

### Step 4: Test Setup / اختبر الإعداد

```bash
# Run test script / شغل سكريبت الاختبار
python test_server.py

# OR / أو
python3 test_server.py
```

**Expected Output:**
```
🔍 Testing Talib-Awn Backend Setup
============================================================
✓ Test 1: Python Version
  ✅ PASS
✓ Test 2: Project Files
  ✅ PASS - All project files found
✓ Test 3: Python Dependencies
  ✅ Flask
  ✅ Flask-SQLAlchemy
  ...
✓ Test 4: Environment Configuration
  ✅ .env file exists
✓ Test 5: Database Connection
  ✅ Database connection successful
✓ Test 6: Flask Application
  ✅ Flask app created successfully
✓ Test 7: Port Availability
  ✅ Port 5000 is available

✅ ALL TESTS PASSED!
```

If any test fails, fix it before continuing.

---

### Step 5: Start Server / شغل الخادم

#### Option A: Using Startup Script (Recommended) / باستخدام سكريبت التشغيل

**Linux/macOS:**
```bash
chmod +x start_server.sh
./start_server.sh
```

**Windows:**
```cmd
start_server.bat
```

#### Option B: Direct / مباشرة

```bash
python app.py
# OR
python3 app.py
```

**Expected Output:**
```
⚠️  WARNING: Using default JWT secret...
✅  Database tables ready.
🚀  Starting Talib-Awn API on http://localhost:5000
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
 * Running on http://localhost:5000
```

**✅ Server is now running!**

---

### Step 6: Verify Server / تحقق من الخادم

#### 6.1: Test Health Check / اختبر صحة الخادم

Open browser and go to:
```
http://localhost:5000/api/
```

**Expected Response:**
```json
{
  "ok": true,
  "message": "Talib-Awn API is running 🚀"
}
```

#### 6.2: Test with curl / اختبر بـ curl

```bash
# Health check
curl http://localhost:5000/api/

# Stats endpoint
curl http://localhost:5000/api/stats

# Test login (should fail with wrong credentials)
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"Test1234"}'
```

---

### Step 7: Connect Frontend / اتصل بالواجهة الأمامية

#### 7.1: Verify API URL in api.js

The API URL has been automatically fixed to:
```javascript
const DEVELOPMENT_API = "http://localhost:5000/api";
```

#### 7.2: Start Frontend / شغل الواجهة الأمامية

**Using VS Code Live Server:**
1. Right-click `index.html`
2. Select "Open with Live Server"
3. Browser opens at `http://localhost:5501` (or similar)

**Using Python:**
```bash
python -m http.server 5501
# Open browser: http://localhost:5501
```

**Using Node.js:**
```bash
npx serve . -p 5501
# Open browser: http://localhost:5501
```

#### 7.3: Test Login / اختبر تسجيل الدخول

1. Open `http://localhost:5501/login.html`
2. Try to login
3. Check browser console (F12) for errors

**Should now work without connection errors!**

---

## 🐛 Still Having Issues? / ما زلت تواجه مشاكل؟

### Issue 1: "Module not found" Error

**Solution:**
```bash
pip install -r requirements.txt --force-reinstall
```

### Issue 2: "Can't connect to MySQL"

**Solution:**
```bash
# Check if MySQL is running
sudo systemctl status mysql  # Linux
brew services list           # macOS

# Start MySQL
sudo systemctl start mysql   # Linux
brew services start mysql    # macOS
net start MySQL              # Windows

# Test connection
mysql -u root -p -e "SELECT 1"
```

### Issue 3: "Port 5000 already in use"

**Solution:**
```bash
# Find process using port 5000
lsof -i :5000  # Linux/macOS
netstat -ano | findstr 5000  # Windows

# Kill the process
kill -9 <PID>  # Linux/macOS
taskkill /PID <PID> /F  # Windows
```

### Issue 4: CORS Errors in Browser

**Solution:**
1. Make sure backend is running: `curl http://localhost:5000/api/`
2. Clear browser cache (Ctrl+Shift+Delete)
3. Clear localStorage: Open Console (F12) → Type `localStorage.clear()` → Enter
4. Restart both backend and frontend

### Issue 5: "Database 'talibawn' doesn't exist"

**Solution:**
```bash
mysql -u root -p -e "CREATE DATABASE talibawn CHARACTER SET utf8mb4;"
```

---

## 📝 Quick Checklist / قائمة التحقق السريعة

Before reporting issues, verify:

- [ ] Python 3.8+ installed: `python --version`
- [ ] MySQL running: `mysql -u root -p -e "SELECT 1"`
- [ ] Dependencies installed: `pip list | grep flask`
- [ ] Database exists: `mysql -u root -p -e "SHOW DATABASES LIKE 'talibawn'"`
- [ ] .env file configured with correct password
- [ ] Port 5000 available: `lsof -i :5000`
- [ ] Server starts without errors
- [ ] Health check returns OK: `curl http://localhost:5000/api/`
- [ ] Frontend uses correct URL: Check api.js
- [ ] Browser console shows no CORS errors (F12)

---

## 🆘 Need More Help? / تحتاج مساعدة إضافية؟

### Check Logs / تحقق من السجلات

```bash
# Server logs (in terminal where you ran python app.py)
# Look for error messages

# OR if running with nohup
tail -f server.log
```

### Common Log Errors / أخطاء شائعة في السجلات

**Error: "Access denied for user 'root'"**
- Fix: Update DB_PASS in .env

**Error: "Unknown database 'talibawn'"**
- Fix: Create database (see Step 2.2)

**Error: "No module named 'flask'"**
- Fix: Install dependencies (see Step 1)

### Documentation / الوثائق

- [Quick Start Guide](QUICK_START.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md)
- [Backend Improvements](BACKEND_IMPROVEMENTS.md)

### Support / الدعم

- **GitHub Issues**: [Open an issue](https://github.com/Rayane-cs/talib-awn/issues)
- **Email**: kessoularayaneayoub@gmail.com

---

## ✅ Success Checklist / قائمة النجاح

You know everything is working when:

✅ `python test_server.py` - All tests pass  
✅ `python app.py` - Server starts without errors  
✅ `curl http://localhost:5000/api/` - Returns `{"ok": true}`  
✅ Browser → http://localhost:5501/login.html - Page loads  
✅ Browser Console (F12) - No red errors  
✅ Try login - Shows "تسجيل الدخول..." (logging in...)  
✅ No "تعذّر الاتصال" errors  

---

**بالتوفيق! Good luck!** 🚀
