# Troubleshooting Guide
**Talib-Awn · طالب عون**

---

## 🔴 CORS Issues

### Error: "No 'Access-Control-Allow-Origin' header present"

**Symptoms:**
```
Access to fetch at 'http://127.0.0.1:5000/api/auth/login' from origin 'http://127.0.0.1:5501' 
has been blocked by CORS policy
```

**Solutions:**

1. **Verify Flask server is running:**
   ```bash
   # Check if port 5000 is listening
   lsof -i :5000
   # OR
   netstat -an | grep 5000
   ```

2. **Check CORS configuration in app.py:**
   - Should allow all origins in development
   - Verify `flask-cors` is installed: `pip list | grep flask-cors`

3. **Restart Flask server:**
   ```bash
   # Stop server (CTRL+C)
   # Then restart
   python app.py
   # OR use the startup script
   ./start_server.sh
   ```

4. **Check server logs for CORS errors**

5. **Test with curl:**
   ```bash
   curl -X OPTIONS http://localhost:5000/api/auth/login \
     -H "Origin: http://127.0.0.1:5501" \
     -H "Access-Control-Request-Method: POST" \
     -v
   ```

---

## 🔴 Connection Refused / Failed to Fetch

### Error: "Failed to fetch" or "net::ERR_FAILED"

**Symptoms:**
```
Failed to load resource: net::ERR_FAILED
:5000/api/auth/login:1 Failed to load resource
```

**Causes:**
- Flask server not running
- Wrong host/port
- Firewall blocking connection

**Solutions:**

1. **Start the Flask server:**
   ```bash
   # Option 1: Direct
   python app.py
   
   # Option 2: With startup script
   ./start_server.sh
   
   # Option 3: Background
   nohup python app.py > server.log 2>&1 &
   ```

2. **Verify server is running:**
   ```bash
   curl http://localhost:5000/api/
   # Should return: {"ok": true, "message": "Talib-Awn API is running 🚀"}
   ```

3. **Check if port 5000 is in use:**
   ```bash
   lsof -i :5000
   # If occupied, kill it:
   kill -9 $(lsof -t -i:5000)
   ```

4. **Try different host:**
   ```javascript
   // In api.js, change API_URL to:
   const API_URL = 'http://localhost:5000/api';  // instead of 127.0.0.1
   ```

---

## 🔴 Database Connection Issues

### Error: "Can't connect to MySQL server"

**Solutions:**

1. **Check MySQL is running:**
   ```bash
   # Linux
   sudo systemctl status mysql
   # OR
   sudo service mysql status
   
   # macOS
   brew services list
   
   # Windows
   net start MySQL
   ```

2. **Start MySQL if stopped:**
   ```bash
   # Linux
   sudo systemctl start mysql
   
   # macOS
   brew services start mysql
   
   # Windows
   net start MySQL
   ```

3. **Verify credentials in .env:**
   ```bash
   DB_USER=root
   DB_PASS=your_password
   DB_HOST=localhost
   DB_NAME=talibawn
   ```

4. **Create database if missing:**
   ```bash
   mysql -u root -p
   CREATE DATABASE talibawn CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   EXIT;
   ```

5. **Test connection:**
   ```bash
   mysql -h localhost -u root -p talibawn
   ```

### Error: "Access denied for user"

**Solutions:**

1. **Check password in .env**
2. **Grant permissions:**
   ```sql
   GRANT ALL PRIVILEGES ON talibawn.* TO 'root'@'localhost';
   FLUSH PRIVILEGES;
   ```

---

## 🔴 Module Import Errors

### Error: "ModuleNotFoundError: No module named 'flask'"

**Solution:**
```bash
# Install all dependencies
pip install -r requirements.txt

# OR install individually
pip install flask flask-sqlalchemy flask-jwt-extended flask-cors pymysql python-dotenv
```

### Error: "No module named 'validators'" or "middleware"

**Cause:** New modules not found

**Solution:**
```bash
# Make sure you're in the project directory
cd /path/to/talib-awn

# Verify files exist
ls -la *.py | grep -E "auth_utils|validators|middleware|db_logger"

# If missing, pull from git
git pull origin main
```

---

## 🔴 JWT Token Issues

### Error: "Signature verification failed"

**Solutions:**

1. **Clear browser localStorage:**
   ```javascript
   // In browser console
   localStorage.clear();
   ```

2. **Check JWT_SECRET consistency:**
   - Verify .env has JWT_SECRET set
   - Don't change JWT_SECRET while users are logged in

3. **Log out and log in again**

### Error: "Token has expired"

**Solution:**
- Use refresh token to get new access token
- Or log in again

---

## 🔴 Rate Limiting Issues

### Error: "Too many attempts. Try again in X seconds"

**Cause:** Rate limiting triggered

**Solutions:**

1. **Wait for cooldown period:**
   - Login: 5 minutes
   - OTP: 3 minutes
   - API: 1 minute

2. **Adjust rate limits (development only):**
   ```python
   # In auth_utils.py
   RATE_LIMIT_LOGIN_MAX = 10  # Increase limit
   RATE_LIMIT_LOGIN_WINDOW = 60  # Reduce window
   ```

3. **Clear rate limit store (restart server):**
   ```bash
   # Stop server
   # Start server (clears in-memory rate limit)
   ```

---

## 🔴 Email/OTP Issues

### Error: "Failed to send email"

**Solutions:**

1. **Check Gmail credentials in .env:**
   ```bash
   GMAIL_ADDRESS=your-email@gmail.com
   GMAIL_APP_PASS=your-app-specific-password
   ```

2. **Generate App Password:**
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate new password for "Mail"

3. **Allow less secure apps (not recommended):**
   - Enable in Google Account settings

4. **Check SMTP connection:**
   ```python
   import smtplib
   with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
       s.login('your-email@gmail.com', 'your-app-password')
       print('✅ SMTP connection successful')
   ```

---

## 🔴 Frontend Issues

### Error: "Unexpected token '<' in JSON"

**Cause:** Getting HTML instead of JSON (404 or error page)

**Solutions:**

1. **Check API endpoint URL:**
   ```javascript
   // Should be:
   const API_URL = 'http://localhost:5000/api';
   // NOT:
   const API_URL = 'http://localhost:5000';
   ```

2. **Verify endpoint exists:**
   ```bash
   curl http://localhost:5000/api/auth/login -X POST \
     -H "Content-Type: application/json" \
     -d '{"email":"test@test.com","password":"test123"}'
   ```

### Frontend not connecting to backend

**Solutions:**

1. **Check API_URL in api.js:**
   ```javascript
   const API_URL = 'http://localhost:5000/api';  // Update if different
   ```

2. **Verify both servers running:**
   - Backend: http://localhost:5000
   - Frontend: http://localhost:5501 (or your Live Server port)

3. **Check browser console for errors**

4. **Test with Postman/curl first**

---

## 🔴 Performance Issues

### Server running slowly

**Solutions:**

1. **Check database connection pool:**
   ```python
   # In app.py - Already configured
   'pool_size': 10,
   'max_overflow': 20,
   ```

2. **Enable query logging to find slow queries:**
   ```python
   # In app.py, add:
   app.config['SQLALCHEMY_ECHO'] = True  # Shows SQL queries
   ```

3. **Check MySQL performance:**
   ```sql
   SHOW PROCESSLIST;
   SHOW STATUS LIKE 'Threads_connected';
   ```

4. **Monitor server:**
   ```bash
   # CPU/Memory usage
   top
   # OR
   htop
   ```

---

## 📝 Common Quick Fixes

### Quick Server Restart
```bash
# Stop server (CTRL+C in terminal)
# Start server
python app.py
```

### Reset Everything
```bash
# 1. Stop server
# 2. Clear database (optional - WARNING: loses data)
mysql -u root -p -e "DROP DATABASE talibawn; CREATE DATABASE talibawn;"
# 3. Clear Python cache
rm -rf __pycache__
# 4. Reinstall dependencies
pip install -r requirements.txt --force-reinstall
# 5. Start server
python app.py
```

### Check Everything
```bash
# 1. Server running?
curl http://localhost:5000/api/

# 2. Database accessible?
mysql -u root -p talibawn -e "SHOW TABLES;"

# 3. Dependencies installed?
pip list | grep -E "flask|pymysql"

# 4. Port available?
lsof -i :5000
```

---

## 🧪 Testing Endpoints

### Test Login
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"Test1234"}'
```

### Test Registration
```bash
curl -X POST http://localhost:5000/api/auth/register/send-otp \
  -H "Content-Type: application/json" \
  -d '{
    "email":"newuser@test.com",
    "password":"Test1234",
    "firstname":"Test",
    "lastname":"User",
    "type":"student",
    "phone":"0555123456"
  }'
```

### Test Health Check
```bash
curl http://localhost:5000/api/
```

### Test Stats
```bash
curl http://localhost:5000/api/stats
```

---

## 📞 Getting Help

If issues persist:

1. **Check logs:**
   ```bash
   # Server logs
   tail -f server.log  # if running with nohup
   # OR check terminal output
   ```

2. **Enable debug mode:**
   ```python
   # In app.py
   app.run(debug=True, port=5000, host='0.0.0.0')
   ```

3. **Review documentation:**
   - BACKEND_IMPROVEMENTS.md
   - DATABASE.md
   - SECURITY.md

4. **Check GitHub issues**

---

## ✅ Prevention Checklist

- [ ] Always start server before testing frontend
- [ ] Check .env file has all required variables
- [ ] Ensure MySQL is running
- [ ] Verify port 5000 is available
- [ ] Clear browser cache/localStorage when testing auth
- [ ] Use consistent URLs (localhost vs 127.0.0.1)
- [ ] Check CORS configuration matches your frontend URL
- [ ] Monitor server logs for errors
- [ ] Test API with curl/Postman before frontend integration

---

**For critical issues, check server logs first - they contain detailed error messages.**
