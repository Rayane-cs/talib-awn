# Security Policy & Guidelines
**Talib-Awn · طالب عون**

Last Updated: 2026-03-23

---

## 🔐 Security Overview

This document outlines security measures, best practices, and policies for the Talib-Awn platform.

---

## 🛡️ Authentication & Authorization

### Password Requirements

**Minimum Requirements:**
- ✅ At least 8 characters
- ✅ Contains at least one letter (a-z, A-Z)
- ✅ Contains at least one number (0-9)
- ✅ Maximum 128 characters

**Implementation:**
- Passwords hashed using `werkzeug.security` (bcrypt algorithm)
- Never stored in plain text
- Never transmitted in logs or error messages

**Recommendations for Users:**
- Use unique passwords
- Include special characters
- Avoid common words or patterns
- Use a password manager

### JWT Tokens

**Access Tokens:**
- Expiry: 7 days
- Used for API authentication
- Stored client-side (localStorage/sessionStorage)

**Refresh Tokens:**
- Expiry: 30 days
- Used to obtain new access tokens
- Should be stored securely

**Best Practices:**
- Set strong `JWT_SECRET` in production
- Rotate secrets periodically
- Implement token blacklisting for logout (future enhancement)
- Use HTTPS in production

### Rate Limiting

Protection against brute force and DDoS attacks:

| Endpoint Type | Max Attempts | Time Window |
|---------------|--------------|-------------|
| Login | 5 | 5 minutes |
| OTP Requests | 3 | 3 minutes |
| General API | 100 | 1 minute |

**Triggered Actions:**
- 429 Too Many Requests response
- Temporary IP-based blocking
- Clear error message with retry time

---

## 🔒 Data Protection

### Personal Information

**Stored Data:**
- Email (unique identifier)
- Password hash (bcrypt)
- Name (first & last)
- Phone number
- Profile image
- Academic/professional details

**Protection Measures:**
- Email validation before storage
- Phone number format validation
- Input sanitization for XSS prevention
- No sensitive data in logs

### Financial Data

**Wallet & Transactions:**
- Balance stored as Decimal(12,2) for accuracy
- All transactions logged immutably
- Escrow system for payment protection
- Withdrawal approval workflow

**Security Measures:**
- Transaction integrity checks
- Double-entry accounting principles
- Admin approval for withdrawals
- Audit trail for all money movements

---

## 🚫 Input Validation

### Server-Side Validation

All user inputs validated server-side:

**Email:**
- RFC-compliant format
- Length: 3-120 characters
- Lowercase normalization

**Strings:**
- Length limits enforced
- HTML tag sanitization
- Null byte removal
- Whitespace trimming

**Numbers:**
- Type checking
- Range validation
- Precision control (money = 2 decimals)

**URLs:**
- Format validation
- Protocol restriction (http/https)
- Length limit (2048 chars)

### SQL Injection Prevention

- ✅ SQLAlchemy ORM used throughout
- ✅ No raw SQL with user input
- ✅ Parameterized queries only
- ✅ Input sanitization before queries

### XSS Prevention

- ✅ HTML escaping in `sanitize_html()`
- ✅ Content-Type headers properly set
- ✅ No eval() or unsafe JavaScript generation
- ✅ User content properly escaped in responses

---

## 🔐 Environment Variables

**Required Variables:**

```bash
# CRITICAL - Must be set in production
JWT_SECRET=<strong-random-256-bit-key>

# Database credentials
DB_USER=<database_username>
DB_PASS=<database_password>
DB_HOST=<database_host>
DB_NAME=talibawn

# Email service (for OTP)
GMAIL_ADDRESS=<your-email@gmail.com>
GMAIL_APP_PASS=<google-app-password>
```

**Security Notes:**
- Never commit `.env` to version control
- Use different secrets per environment
- Rotate secrets regularly (quarterly recommended)
- Use environment-specific configurations

---

## 🌐 API Security

### CORS Configuration

Current settings:
```python
CORS(app, resources={r'/api/*': {'origins': '*'}}, supports_credentials=True)
```

**Production Recommendations:**
- Replace `'*'` with specific allowed origins
- Use environment variable for allowed origins
- Example: `ALLOWED_ORIGINS=https://talibawn.com,https://app.talibawn.com`

### HTTPS/TLS

**Requirements:**
- Use HTTPS in production (enforced at deployment level)
- Redirect HTTP to HTTPS
- Use TLS 1.2 or higher
- Valid SSL certificate from trusted CA

### Headers

**Recommended Security Headers:**
```python
# Add to app.py or middleware
@app.after_request
def security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response
```

---

## 👤 User Account Security

### Account States

**is_verified:**
- Default: `True`
- Email verification can be enforced in future

**is_banned:**
- Admin can ban accounts
- Banned users cannot log in
- Ban reason stored and displayed

**warnings:**
- Progressive warning system
- Auto-ban after 3 warnings
- Admin can issue warnings

### Ban System

**Triggers:**
- Manual admin action
- Automatic after 3 warnings
- Violation of terms of service

**Effects:**
- Login blocked
- API access denied
- Clear error message shown

---

## 💰 Financial Security

### Wallet System

**Protection Measures:**
- Balance stored with 2 decimal precision
- Atomic transaction operations
- Double-entry accounting
- Transaction immutability

**Limits:**
- Minimum deposit: 100 DZD
- Maximum deposit: 200,000 DZD
- Minimum withdrawal: 500 DZD

### Escrow System

**Flow:**
1. Employer deposits funds (held in escrow)
2. Student completes work
3. Employer releases funds (or cancels)
4. Funds transferred to student wallet

**Security:**
- Funds locked during escrow
- Only employer can release/cancel
- Full audit trail
- Transaction records immutable

### Withdrawal Approval

**Workflow:**
1. User requests withdrawal
2. Funds deducted immediately from wallet
3. Admin reviews request
4. Admin approves or rejects
5. If rejected, funds refunded

**Security:**
- Admin approval required
- Account number validation
- Payout method verification
- Rejection reason required

---

## 📊 Logging & Monitoring

### What Gets Logged

**Request Logging:**
- HTTP method and path
- Client IP address
- Response status code
- Request duration

**Error Logging:**
- Exception type and message
- Stack trace (server-side only)
- Request context
- Timestamp

**Security Events:**
- Failed login attempts
- Rate limit violations
- Admin actions (ban, unban, warn)
- Financial transactions

### What NOT to Log

- ❌ Passwords (plain or hashed)
- ❌ JWT tokens
- ❌ Email content
- ❌ Personal identifiable information
- ❌ Payment details

---

## 🚨 Incident Response

### Suspected Breach

1. **Immediate Actions:**
   - Disable affected accounts
   - Rotate JWT secret
   - Review recent transactions
   - Check server logs

2. **Investigation:**
   - Identify breach scope
   - Determine attack vector
   - Document timeline
   - Preserve evidence

3. **Remediation:**
   - Patch vulnerabilities
   - Force password resets
   - Notify affected users
   - Update security measures

### Reporting Security Issues

**Contact:**
- Email: security@talibawn.com (if available)
- Create private GitHub issue
- Direct contact with maintainers

**Information to Include:**
- Vulnerability description
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

---

## ✅ Security Checklist

### Pre-Deployment

- [ ] Set strong `JWT_SECRET`
- [ ] Configure CORS for production domains
- [ ] Enable HTTPS/TLS
- [ ] Set up security headers
- [ ] Configure rate limiting
- [ ] Review database permissions
- [ ] Set up monitoring and alerts
- [ ] Test authentication flows
- [ ] Verify input validation
- [ ] Check error messages (no info leakage)

### Regular Maintenance

- [ ] Rotate JWT secret (quarterly)
- [ ] Update dependencies (monthly)
- [ ] Review access logs (weekly)
- [ ] Audit financial transactions (weekly)
- [ ] Test backup restoration (monthly)
- [ ] Security vulnerability scan (monthly)
- [ ] Review user permissions (quarterly)

### Incident Response

- [ ] Document incident response plan
- [ ] Designate security team contacts
- [ ] Set up monitoring alerts
- [ ] Prepare communication templates
- [ ] Test backup systems
- [ ] Review insurance coverage

---

## 🔍 Vulnerability Disclosure

We take security seriously. If you discover a vulnerability:

1. **Do NOT** publicly disclose it
2. Report it privately to maintainers
3. Allow reasonable time for fix (90 days)
4. Coordinate disclosure timing

**Acknowledgment:**
- We appreciate responsible disclosure
- Credit given in changelog (if desired)
- No bug bounty program currently

---

## 📚 Security Resources

### Dependencies

Keep these updated for security patches:
- Flask
- SQLAlchemy
- Flask-JWT-Extended
- Werkzeug
- PyMySQL

### References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Flask Security](https://flask.palletsprojects.com/en/latest/security/)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)

---

## 📝 Compliance

### Data Protection

- User data minimization
- Right to access (GET /api/auth/me)
- Right to deletion (on request)
- Data portability support

### Algerian Regulations

- Comply with local data protection laws
- Secure financial transaction handling
- User consent for data collection
- Transparent privacy policy

---

**For security questions or concerns, please contact the development team.**

**End of Security Policy**
