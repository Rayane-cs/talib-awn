# Talib-Awn — Supabase → MySQL Migration Guide

## Files generated
| File | Purpose |
|---|---|
| `models_talib.py` | SQLAlchemy models (all tables) |
| `routes_talib.py` | Flask API blueprint (all endpoints) |
| `app_talib.py`    | Flask app factory + MySQL config |
| `api.js`          | Frontend client (replaces supabase.js) |

---

## Step 1 — Install Python packages
```
pip install flask flask-sqlalchemy flask-jwt-extended flask-cors pymysql
```

## Step 2 — Create the MySQL database
```sql
CREATE DATABASE talibawn CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

## Step 3 — Set environment variables
Create a `.env` file (or set in your system):
```
DB_USER=root
DB_PASS=yourpassword
DB_HOST=localhost
DB_NAME=talibawn
JWT_SECRET=some-very-long-random-string
GMAIL_ADDRESS=universitychlefclub@gmail.com
GMAIL_APP_PASS=rqki cvlk iqgr smdj
```
Load it with `python-dotenv` or export manually.

## Step 4 — Merge with your existing project
If your friend's project already has `app.py`, `models.py`, `routes.py`:

1. **models.py** — paste the new classes from `models_talib.py` at the bottom
   (they share the same `db` instance)

2. **app.py** — add this block:
   ```python
   from routes_talib import talib_bp
   app.register_blueprint(talib_bp, url_prefix='/api')
   ```

3. Run once to create tables:
   ```python
   with app.app_context():
       db.create_all()
   ```

## Step 5 — Replace supabase.js in HTML files
In every HTML file change:
```html
<!-- OLD -->
<script type="module">
  import { ... } from './supabase.js';

<!-- NEW -->
<script type="module">
  import { ... } from './api.js';
```

Also update `wallet.js` to import from `./api.js` instead of `./supabase.js`.

## Step 6 — Update forgot-password.html for reset flow
The new 3-step reset stores email/OTP on `window` so `updatePassword()` can use it.
Add these two lines in your verify-OTP handler:
```js
window._resetEmail = email;
window._resetOtp   = otp;   // after verifyPasswordResetOtp succeeds
```

## Step 7 — Run the server
```
python app_talib.py
# or with python-dotenv:
flask --app app_talib:create_app run --debug
```

---

## API Endpoint Reference

### Auth
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/auth/register/send-otp` | Start registration, send OTP |
| POST | `/api/auth/register/verify-otp` | Verify OTP, create user + JWT |
| POST | `/api/auth/login` | Email + password login |
| POST | `/api/auth/refresh` | Refresh access token |
| GET  | `/api/auth/me` | Get current user profile |
| POST | `/api/auth/reset/send-otp` | Password reset step 1 |
| POST | `/api/auth/reset/verify-otp` | Password reset step 2 |
| POST | `/api/auth/reset/set-password` | Password reset step 3 |

### Users
| POST | `/api/users/me` PATCH | Edit profile |
| GET  | `/api/users/<id>` | Public profile + projects |
| GET  | `/api/users/search?q=name` | Search users |
| POST | `/api/users/<id>/follow` | Toggle follow |

### Projects / Events / Announcements
| GET/POST | `/api/projects` | List / create |
| PATCH/DELETE | `/api/projects/<id>` | Edit / delete |
| POST | `/api/projects/<id>/like` | Toggle like |
| GET/POST | `/api/projects/<id>/comments` | List / add comment |
| DELETE | `/api/comments/<id>` | Delete comment |
| GET | `/api/events` | List events |
| POST/DELETE | `/api/events/<id>/register` | Join / quit event |
| GET | `/api/announcements` | List announcements |
| GET | `/api/stats` | Platform stats |

### Wallet
| GET | `/api/wallet` | Balance |
| GET | `/api/wallet/transactions` | Transaction history |
| POST | `/api/wallet/deposit` | Request manual deposit |
| POST | `/api/wallet/withdraw` | Request withdrawal |
| GET | `/api/wallet/withdrawals` | Withdrawal history |
| POST | `/api/escrow` | Create escrow |
| POST | `/api/escrow/<id>/release` | Release escrow to student |
| POST | `/api/escrow/<id>/cancel` | Cancel + refund |
| GET | `/api/escrow/as-employer` | Employer escrows |
| GET | `/api/escrow/as-student` | Student incoming |
| POST | `/api/webhook/chargily` | Chargily payment webhook |

### Admin
| GET | `/api/admin/users` | All non-admin users |
| POST | `/api/admin/users/<id>/ban` | Ban user |
| POST | `/api/admin/users/<id>/unban` | Unban user |
| POST | `/api/admin/users/<id>/warn` | Warn user (3 = auto-ban) |
| GET | `/api/admin/withdrawals` | All withdrawal requests |
| POST | `/api/admin/withdrawals/<id>/approve` | Approve withdrawal |
| POST | `/api/admin/withdrawals/<id>/reject` | Reject + refund |
| POST | `/api/admin/events` | Create event + email all users |
| POST | `/api/admin/announcements` | Create announcement |
