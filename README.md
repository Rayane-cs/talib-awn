# Talib-Awn · طالب عون
**Student Support Platform for Algeria**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.3+-green.svg)](https://flask.palletsprojects.com/)
[![MySQL](https://img.shields.io/badge/MySQL-5.7+-orange.svg)](https://www.mysql.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A comprehensive platform connecting students with opportunities, projects, and employers in Algeria. Built with Flask, SQLAlchemy, and modern security practices.

---

## ✨ Features

### For Students
- 🎓 **Profile Management** - Showcase your academic background and skills
- 💼 **Project Portfolio** - Share and discover student projects
- 🎯 **Event Registration** - Join workshops, hackathons, and webinars
- 💰 **Wallet System** - Earn and manage payments securely
- 🤝 **Social Network** - Follow peers and build connections

### For Employers
- 👥 **Talent Discovery** - Find skilled students for projects
- 💳 **Secure Payments** - Escrow system for safe transactions
- 📢 **Post Opportunities** - Share jobs and collaborations
- 📊 **Dashboard** - Manage interactions and payments

### Platform Features
- 🔒 **Secure Authentication** - JWT tokens, rate limiting, OTP verification
- 📧 **Email Notifications** - Registration, events, follows
- 🌐 **RESTful API** - Clean, documented endpoints
- 📱 **Responsive Design** - Mobile-friendly interface
- 🇩🇿 **Algerian Context** - Local payment methods, phone formats

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- MySQL 5.7+
- pip

### Installation

```bash
# 1. Clone repository
git clone https://github.com/Rayane-cs/talib-awn.git
cd talib-awn

# 2. Run startup script
./start_server.sh        # Linux/macOS
start_server.bat         # Windows

# 3. Open browser
http://localhost:5000/api/
```

**That's it!** See [QUICK_START.md](QUICK_START.md) for detailed instructions.

---

## 📋 Table of Contents

- [Architecture](#-architecture)
- [API Documentation](#-api-documentation)
- [Database Schema](#-database-schema)
- [Security](#-security)
- [Development](#-development)
- [Deployment](#-deployment)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🏗️ Architecture

### Tech Stack

**Backend:**
- Flask 2.3+ (Web framework)
- SQLAlchemy 2.0+ (ORM)
- MySQL 5.7+ (Database)
- Flask-JWT-Extended (Authentication)
- Flask-CORS (Cross-origin support)

**Frontend:**
- Vanilla JavaScript
- HTML5 + CSS3
- Responsive design

### Project Structure

```
talib-awn/
├── app.py                    # Flask application entry point
├── models.py                 # SQLAlchemy models (14 tables)
├── routes.py                 # API endpoints (49 routes)
├── auth_utils.py             # Auth utilities & rate limiting
├── validators.py             # Input validation framework
├── middleware.py             # Error handling & logging
├── db_logger.py              # Database change tracking
├── parsers.py                # Request parsing helpers
├── requirements.txt          # Python dependencies
├── .env                      # Environment configuration
├── start_server.sh           # Linux/macOS startup
├── start_server.bat          # Windows startup
├── DATABASE.md               # Complete schema docs
├── BACKEND_IMPROVEMENTS.md   # Architecture guide
├── SECURITY.md               # Security policies
├── TROUBLESHOOTING.md        # Common issues & fixes
└── QUICK_START.md            # Setup guide
```

### Key Components

**Authentication System:**
- JWT-based authentication
- OTP verification (email)
- Rate limiting (login, OTP, API)
- Password strength validation
- Ban/warning system

**Financial System:**
- User wallets (DZD)
- Escrow for job payments
- Withdrawal approval workflow
- Transaction history
- Multiple payout methods (CCP, Edahabia, Baridi Mob)

**Social Features:**
- User following
- Project likes & comments
- Event registrations
- Announcements

---

## 📡 API Documentation

### Base URL
```
http://localhost:5000/api
```

### Authentication Endpoints

#### Register (with OTP)
```http
POST /auth/register/send-otp
Content-Type: application/json

{
  "email": "student@university.dz",
  "password": "SecurePass123",
  "firstname": "Ahmed",
  "lastname": "Benali",
  "type": "student",
  "grade": "Student",
  "domain": "intelligence artificielle",
  "phone": "0555123456"
}
```

#### Login
```http
POST /auth/login
Content-Type: application/json

{
  "email": "student@university.dz",
  "password": "SecurePass123"
}

Response:
{
  "ok": true,
  "data": {
    "user": { ... },
    "access_token": "eyJ...",
    "refresh_token": "eyJ..."
  }
}
```

#### Get Current User
```http
GET /auth/me
Authorization: Bearer <access_token>
```

### Project Endpoints

#### List Projects
```http
GET /projects?category=developpement web
```

#### Create Project
```http
POST /projects
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "AI Chatbot for Students",
  "description": "Smart assistant for academic help",
  "category": "intelligence artificielle",
  "status": "open"
}
```

### Wallet Endpoints

#### Get Balance
```http
GET /wallet
Authorization: Bearer <token>
```

#### Request Withdrawal
```http
POST /wallet/withdraw
Authorization: Bearer <token>
Content-Type: application/json

{
  "amount": 5000,
  "payout_method": "ccp",
  "account_number": "0012345678901234567"
}
```

**Full API documentation:** See [BACKEND_IMPROVEMENTS.md](BACKEND_IMPROVEMENTS.md)

---

## 🗄️ Database Schema

### Core Tables
- **users** - Base user identity & auth
- **students** - Student profiles (joined inheritance)
- **employers** - Employer profiles (joined inheritance)
- **projects** - User projects
- **events** - Platform events
- **wallets** - User balances
- **transactions** - Financial history
- **escrows** - Payment holds

**14 tables total.** See [DATABASE.md](DATABASE.md) for complete schema.

### ERD Overview
```
users (base)
├── students (1:1)
├── employers (1:1)
├── projects (1:N)
├── wallets (1:1)
└── transactions (1:N)

projects
├── project_likes (1:N)
└── project_comments (1:N)

events
└── event_registrations (1:N)
```

---

## 🔒 Security

### Features Implemented

✅ **Authentication**
- JWT tokens (7-day access, 30-day refresh)
- Bcrypt password hashing
- OTP verification via email
- Rate limiting (5 login attempts per 5 min)

✅ **Input Validation**
- Email format validation
- Phone number validation (Algerian)
- Password strength (8+ chars, letters + numbers)
- SQL injection prevention (ORM only)
- XSS prevention (HTML sanitization)

✅ **API Security**
- CORS configured properly
- Rate limiting per IP
- Request/response logging
- Error handling (no info leakage)

✅ **Financial Security**
- Escrow system
- Admin approval for withdrawals
- Transaction immutability
- Decimal precision for money

**Full security policy:** See [SECURITY.md](SECURITY.md)

---

## 💻 Development

### Setup Development Environment

```bash
# 1. Clone and navigate
git clone https://github.com/Rayane-cs/talib-awn.git
cd talib-awn

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create database
mysql -u root -p -e "CREATE DATABASE talibawn CHARACTER SET utf8mb4;"

# 5. Configure .env
cp .env.example .env
# Edit .env with your settings

# 6. Run server
python app.py
```

### Development Tools

**Auto-reload:**
```bash
export FLASK_DEBUG=1
python app.py
```

**Database migrations:**
```python
from db_logger import DatabaseLogger
DatabaseLogger.log_column_addition('users', 'last_login', 'DateTime')
```

**Testing:**
```bash
# Test endpoints with curl
curl http://localhost:5000/api/stats

# Or use Postman/Insomnia
```

### Code Structure

**Adding a new endpoint:**
```python
# In routes.py
@bp.get('/custom/endpoint')
@jwt_required(optional=True)
@handle_errors
def custom_endpoint():
    user = _current_user()
    # Your logic here
    return _ok({'data': 'value'})
```

**Adding validation:**
```python
# In validators.py
def validate_custom_data(data: dict) -> dict:
    v = Validator()
    return {
        'field': v.validate_string(data.get('field'), 'Field Name', min_length=3)
    }
```

---

## 🚢 Deployment

### Production Setup

1. **Environment Variables**
```bash
export JWT_SECRET="<strong-random-secret>"
export DB_PASS="<secure-password>"
export GMAIL_APP_PASS="<app-password>"
```

2. **Database**
```bash
# Create production database
mysql -u root -p -e "CREATE DATABASE talibawn CHARACTER SET utf8mb4;"

# Run migrations if any
python app.py  # Creates tables automatically
```

3. **Run with Gunicorn**
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app --log-file=server.log
```

4. **Nginx Configuration**
```nginx
server {
    listen 80;
    server_name api.talibawn.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

5. **HTTPS with Let's Encrypt**
```bash
sudo certbot --nginx -d api.talibawn.com
```

### Production Checklist

- [ ] Set strong JWT_SECRET
- [ ] Configure CORS for production domain
- [ ] Enable HTTPS
- [ ] Set up log rotation
- [ ] Configure firewall
- [ ] Set up monitoring
- [ ] Configure backups
- [ ] Review rate limits
- [ ] Test all endpoints
- [ ] Load testing

---

## 🤝 Contributing

We welcome contributions! Here's how:

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Make your changes**
4. **Test thoroughly**
5. **Commit with clear message**
   ```bash
   git commit -m "feat: Add amazing feature"
   ```
6. **Push to your fork**
   ```bash
   git push origin feature/amazing-feature
   ```
7. **Open a Pull Request**

### Commit Message Format
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `style:` Formatting
- `refactor:` Code restructuring
- `test:` Tests
- `chore:` Maintenance

---

## 📊 Statistics

- **~5,000 lines** of backend code
- **49 API endpoints**
- **14 database tables**
- **10+ security features**
- **8 reusable decorators**
- **15+ validators**

---

## 📖 Documentation

- [Quick Start Guide](QUICK_START.md) - Get started in 5 minutes
- [Backend Improvements](BACKEND_IMPROVEMENTS.md) - Architecture & features
- [Database Schema](DATABASE.md) - Complete table reference
- [Security Policy](SECURITY.md) - Security practices
- [Troubleshooting](TROUBLESHOOTING.md) - Common issues & fixes

---

## 📝 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

---

## 👥 Authors

- **Rayane Kessoula** - *Initial work* - [@Rayane-cs](https://github.com/Rayane-cs)

---

## 🙏 Acknowledgments

- University of Chlef Computer Science Club
- Algerian student community
- Open source contributors

---

## 📞 Support

- **Email**: kessoularayaneayoub@gmail.com
- **GitHub Issues**: [Open an issue](https://github.com/Rayane-cs/talib-awn/issues)
- **Documentation**: See MD files in repository

---

## 🗺️ Roadmap

### Phase 1 (Current)
- [x] Core authentication system
- [x] Project management
- [x] Wallet & payments
- [x] Events system
- [x] Social features

### Phase 2 (Planned)
- [ ] Two-factor authentication
- [ ] Real-time messaging
- [ ] Job board
- [ ] Skills endorsement
- [ ] Mobile app (React Native)

### Phase 3 (Future)
- [ ] AI-powered matching
- [ ] Video interviews
- [ ] Analytics dashboard
- [ ] API for third-party integrations
- [ ] Multi-language support

---

<div align="center">

**Made with ❤️ for Algerian Students**

[Website](https://talibawn.com) • [API Docs](BACKEND_IMPROVEMENTS.md) • [Report Bug](https://github.com/Rayane-cs/talib-awn/issues)

</div>
