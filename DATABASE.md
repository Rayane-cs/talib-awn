# Database Schema Documentation
**Talib-Awn · طالب عون**

Last Updated: 2026-03-23  
Database: MySQL (PyMySQL)  
ORM: SQLAlchemy with Joined Table Inheritance

---

## 📋 Overview

This document provides a comprehensive overview of the database schema for the Talib-Awn platform. The database uses **Joined Table Inheritance** for user types (Student, Employer) with a shared `users` base table.

---

## 🗂️ Tables

### 1. **users** (Base Identity Table)
Stores core user authentication and profile information.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | Integer | PRIMARY KEY, AUTO_INCREMENT | Unique user identifier |
| `type` | String(20) | NOT NULL, DEFAULT='user' | Discriminator: 'user', 'student', 'employer', 'admin' |
| `email` | String(120) | UNIQUE, NOT NULL, INDEX | User email (login identifier) |
| `password_hash` | String(256) | NOT NULL | Bcrypt hashed password |
| `firstname` | String(80) | NOT NULL | User's first name |
| `lastname` | String(80) | NOT NULL, DEFAULT='' | User's last name |
| `phone` | String(30) | NULLABLE | Phone number |
| `image` | Text | NULLABLE | Profile image URL or base64 |
| `is_verified` | Boolean | DEFAULT=TRUE | Email verification status |
| `is_banned` | Boolean | DEFAULT=FALSE | Ban status |
| `ban_reason` | Text | NULLABLE | Reason for ban (if applicable) |
| `warnings` | Integer | DEFAULT=0 | Number of warnings received |
| `created_at` | DateTime | DEFAULT=CURRENT_TIMESTAMP | Account creation timestamp |
| `updated_at` | DateTime | DEFAULT=CURRENT_TIMESTAMP, ON UPDATE | Last update timestamp |

**Indexes:**
- PRIMARY: `id`
- UNIQUE: `email`

---

### 2. **students** (Joined Table)
Extended profile for student users. Uses Joined Table Inheritance.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | Integer | PRIMARY KEY, FOREIGN KEY → users.id | References user.id |
| `grade` | String(40) | NOT NULL, DEFAULT='Student' | Academic level (Student, Professor, Researcher, Company manager) |
| `domain` | String(80) | NOT NULL, DEFAULT='autre' | Field of interest |
| `institution` | String(120) | NULLABLE | University/institution name |
| `field_of_study` | String(120) | NULLABLE | Major or specialization |
| `student_id_number` | String(60) | NULLABLE | Student ID card number |

**Valid Grades:**
- Student
- Professor
- Researcher
- Company manager

**Valid Domains:**
- intelligence artificielle
- developpement web
- cyber securite
- reseaux et telecommunications
- systemes embarques
- science des donnees
- genie logiciel
- autre

---

### 3. **employers** (Joined Table)
Extended profile for employer users.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | Integer | PRIMARY KEY, FOREIGN KEY → users.id | References user.id |
| `company_name` | String(120) | NULLABLE | Company/organization name |
| `domain` | String(80) | NOT NULL, DEFAULT='autre' | Business domain |

---

### 4. **projects**
User-created projects showcase.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | Integer | PRIMARY KEY, AUTO_INCREMENT | Unique project ID |
| `title` | String(200) | NOT NULL | Project title |
| `description` | Text | NULLABLE | Detailed description |
| `image` | Text | NULLABLE | Cover image URL |
| `category` | String(60) | DEFAULT='autre' | Project category |
| `status` | String(30) | DEFAULT='open' | Project status (open, closed, etc.) |
| `owner_id` | Integer | FOREIGN KEY → users.id, NOT NULL, INDEX | Creator's user ID |
| `is_visible` | Boolean | DEFAULT=TRUE | Visibility flag |
| `created_at` | DateTime | DEFAULT=CURRENT_TIMESTAMP | Creation timestamp |

**Relationships:**
- `owner_id` → `users.id` (CASCADE on delete)

---

### 5. **project_likes**
Tracks user likes on projects.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | Integer | PRIMARY KEY, AUTO_INCREMENT | Unique like ID |
| `project_id` | Integer | FOREIGN KEY → projects.id, INDEX | Referenced project |
| `user_id` | Integer | FOREIGN KEY → users.id, INDEX | User who liked |
| `created_at` | DateTime | DEFAULT=CURRENT_TIMESTAMP | When like was created |

**Constraints:**
- UNIQUE(`project_id`, `user_id`) - One like per user per project
- CASCADE on delete for both foreign keys

---

### 6. **project_comments**
Comments on projects.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | Integer | PRIMARY KEY, AUTO_INCREMENT | Unique comment ID |
| `project_id` | Integer | FOREIGN KEY → projects.id, INDEX | Referenced project |
| `user_id` | Integer | FOREIGN KEY → users.id, INDEX | Commenter's user ID |
| `content` | Text | NOT NULL | Comment text |
| `created_at` | DateTime | DEFAULT=CURRENT_TIMESTAMP | Comment timestamp |

**Relationships:**
- CASCADE on delete for both foreign keys

---

### 7. **events**
Platform events (workshops, webinars, etc.).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | Integer | PRIMARY KEY, AUTO_INCREMENT | Unique event ID |
| `title` | String(200) | NOT NULL | Event name |
| `description` | Text | NULLABLE | Event details |
| `image` | Text | NULLABLE | Event banner/poster |
| `location` | String(200) | NULLABLE | Physical or virtual location |
| `start_at` | DateTime | NULLABLE | Event start time |
| `end_at` | DateTime | NULLABLE | Event end time |
| `event_type` | String(40) | DEFAULT='other' | Event category |
| `capacity` | Integer | NULLABLE | Max attendees (null = unlimited) |
| `is_visible` | Boolean | DEFAULT=TRUE | Visibility status |
| `created_at` | DateTime | DEFAULT=CURRENT_TIMESTAMP | Creation timestamp |

---

### 8. **event_registrations**
User registrations for events.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | Integer | PRIMARY KEY, AUTO_INCREMENT | Unique registration ID |
| `event_id` | Integer | FOREIGN KEY → events.id, INDEX | Referenced event |
| `user_id` | Integer | FOREIGN KEY → users.id, INDEX | Registered user |
| `created_at` | DateTime | DEFAULT=CURRENT_TIMESTAMP | Registration timestamp |

**Constraints:**
- UNIQUE(`event_id`, `user_id`) - One registration per user per event
- CASCADE on delete for both foreign keys

---

### 9. **announcements**
Platform-wide announcements (admin only).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | Integer | PRIMARY KEY, AUTO_INCREMENT | Unique announcement ID |
| `title` | String(200) | NOT NULL, DEFAULT='' | Announcement title |
| `content` | Text | NOT NULL | Announcement body |
| `image` | Text | NULLABLE | Optional image |
| `is_pinned` | Boolean | DEFAULT=FALSE | Pin to top flag |
| `is_visible` | Boolean | DEFAULT=TRUE | Visibility flag |
| `author_id` | Integer | FOREIGN KEY → users.id, NULLABLE | Admin who created it |
| `created_at` | DateTime | DEFAULT=CURRENT_TIMESTAMP | Creation timestamp |

---

### 10. **user_follows**
Social following relationships.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | Integer | PRIMARY KEY, AUTO_INCREMENT | Unique follow ID |
| `follower_id` | Integer | FOREIGN KEY → users.id, INDEX | User who follows |
| `following_id` | Integer | FOREIGN KEY → users.id, INDEX | User being followed |
| `created_at` | DateTime | DEFAULT=CURRENT_TIMESTAMP | Follow timestamp |

**Constraints:**
- UNIQUE(`follower_id`, `following_id`) - One follow per pair
- CASCADE on delete for both foreign keys

---

### 11. **wallets**
User wallet balances (in DZD).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | Integer | PRIMARY KEY, AUTO_INCREMENT | Unique wallet ID |
| `user_id` | Integer | FOREIGN KEY → users.id, UNIQUE, NOT NULL | Wallet owner |
| `balance` | Numeric(12,2) | DEFAULT=0.0 | Current balance in DZD |
| `updated_at` | DateTime | DEFAULT=CURRENT_TIMESTAMP, ON UPDATE | Last balance update |

**Note:** Balances are stored with 2 decimal precision. Automatically created on user registration.

---

### 12. **transactions**
Financial transaction history.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | Integer | PRIMARY KEY, AUTO_INCREMENT | Unique transaction ID |
| `user_id` | Integer | FOREIGN KEY → users.id, NOT NULL, INDEX | User performing transaction |
| `type` | String(20) | NOT NULL | Transaction type |
| `amount` | Numeric(12,2) | NOT NULL | Transaction amount in DZD |
| `status` | String(20) | NOT NULL, DEFAULT='pending' | Transaction status |
| `reference` | String(120) | NULLABLE | External reference (payment gateway) |
| `created_at` | DateTime | DEFAULT=CURRENT_TIMESTAMP | Transaction timestamp |

**Transaction Types:**
- `deposit` - Adding funds to wallet
- `escrow` - Funds held in escrow
- `release` - Escrow released to student
- `refund` - Funds returned to user
- `withdraw` - Withdrawal request

**Transaction Statuses:**
- `pending` - Awaiting confirmation
- `completed` - Successfully processed
- `failed` - Transaction failed

---

### 13. **escrows**
Held funds for job payments (employer → student).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | Integer | PRIMARY KEY, AUTO_INCREMENT | Unique escrow ID |
| `employer_id` | Integer | FOREIGN KEY → users.id, NOT NULL, INDEX | Employer holding funds |
| `student_id` | Integer | FOREIGN KEY → users.id, NOT NULL, INDEX | Student to receive funds |
| `amount` | Numeric(12,2) | NOT NULL | Escrow amount in DZD |
| `status` | String(20) | NOT NULL, DEFAULT='held' | Escrow status |
| `job_id` | Integer | NULLABLE | Related job/project ID (optional) |
| `note` | Text | NULLABLE | Additional notes |
| `created_at` | DateTime | DEFAULT=CURRENT_TIMESTAMP | Escrow creation timestamp |

**Escrow Statuses:**
- `held` - Funds held in escrow
- `released` - Funds released to student
- `cancelled` - Escrow cancelled, funds returned

---

### 14. **withdrawals**
User withdrawal requests (wallet → bank account).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | Integer | PRIMARY KEY, AUTO_INCREMENT | Unique withdrawal ID |
| `user_id` | Integer | FOREIGN KEY → users.id, NOT NULL, INDEX | User requesting withdrawal |
| `amount` | Numeric(12,2) | NOT NULL | Withdrawal amount in DZD |
| `payout_method` | String(20) | NOT NULL, DEFAULT='ccp' | Payment method |
| `account_number` | String(120) | NOT NULL | Destination account number |
| `status` | String(20) | NOT NULL, DEFAULT='pending' | Withdrawal status |
| `admin_note` | Text | NULLABLE | Admin notes (approval/rejection reason) |
| `created_at` | DateTime | DEFAULT=CURRENT_TIMESTAMP | Request timestamp |

**Payout Methods:**
- `ccp` - CCP account
- `edahabia` - Edahabia card
- `baridimob` - Baridi Mob

**Withdrawal Statuses:**
- `pending` - Awaiting admin review
- `approved` - Approved and processed
- `rejected` - Rejected by admin

**Business Rules:**
- Minimum withdrawal: 500 DZD
- Withdrawals deducted from wallet immediately
- Refunded if rejected by admin

---

## 🔗 Relationships Diagram

```
users (base)
├── students (1:1 joined)
├── employers (1:1 joined)
├── projects (1:N via owner_id)
├── project_likes (1:N via user_id)
├── project_comments (1:N via user_id)
├── event_registrations (1:N via user_id)
├── announcements (1:N via author_id)
├── user_follows (follower & following)
├── wallets (1:1)
├── transactions (1:N)
├── escrows (employer & student)
└── withdrawals (1:N)

projects
├── project_likes (1:N)
└── project_comments (1:N)

events
└── event_registrations (1:N)
```

---

## 🔐 Security Considerations

1. **Password Storage**: All passwords hashed using `werkzeug.security.generate_password_hash` (bcrypt)
2. **JWT Authentication**: Access tokens (7 days), Refresh tokens (30 days)
3. **Cascade Deletes**: Proper CASCADE configured for related records
4. **Unique Constraints**: Prevent duplicate likes, follows, registrations
5. **Indexes**: Optimized queries on foreign keys and email lookups

---

## 📝 Change Log

### 2026-03-23 - Database Initialized
**Author:** System  
**Time:** 2026-03-23 20:22:59 UTC  
**Description:** All tables created and database ready for use
### 2026-03-23 - Database Initialized
**Author:** System  
**Time:** 2026-03-23 20:22:44 UTC  
**Description:** All tables created and database ready for use
### 2026-03-23 - Database Initialized
**Author:** System  
**Time:** 2026-03-23 20:22:28 UTC  
**Description:** All tables created and database ready for use
### 2026-03-23 - Database Initialized
**Author:** System  
**Time:** 2026-03-23 20:22:01 UTC  
**Description:** All tables created and database ready for use
### 2026-03-23 - Database Initialized
**Author:** System  
**Time:** 2026-03-23 20:14:26 UTC  
**Description:** All tables created and database ready for use
### 2026-03-23 - Database Initialized
**Author:** System  
**Time:** 2026-03-23 20:11:55 UTC  
**Description:** All tables created and database ready for use
### 2026-03-23 - Database Initialized
**Author:** System  
**Time:** 2026-03-23 20:09:58 UTC  
**Description:** All tables created and database ready for use
### 2026-03-23 - Database Initialized
**Author:** System  
**Time:** 2026-03-23 20:06:03 UTC  
**Description:** All tables created and database ready for use
### 2026-03-23 - Database Initialized
**Author:** System  
**Time:** 2026-03-23 20:05:48 UTC  
**Description:** All tables created and database ready for use
### 2026-03-23 - Database Initialized
**Author:** System  
**Time:** 2026-03-23 20:05:34 UTC  
**Description:** All tables created and database ready for use
### 2026-03-23 - Database Initialized
**Author:** System  
**Time:** 2026-03-23 20:05:12 UTC  
**Description:** All tables created and database ready for use
### 2026-03-23 - Database Initialized
**Author:** System  
**Time:** 2026-03-23 20:04:46 UTC  
**Description:** All tables created and database ready for use
### 2026-03-23 - Database Initialized
**Author:** System  
**Time:** 2026-03-23 19:42:57 UTC  
**Description:** All tables created and database ready for use
### 2026-03-23 - Database Initialized
**Author:** System  
**Time:** 2026-03-23 19:42:53 UTC  
**Description:** All tables created and database ready for use
### 2026-03-23 - Database Initialized
**Author:** System  
**Time:** 2026-03-23 19:42:43 UTC  
**Description:** All tables created and database ready for use
### 2026-03-23 - Database Initialized
**Author:** System  
**Time:** 2026-03-23 19:42:43 UTC  
**Description:** All tables created and database ready for use
### 2026-03-23 - Database Initialized
**Author:** System  
**Time:** 2026-03-23 19:41:45 UTC  
**Description:** All tables created and database ready for use
### 2026-03-23 - Initial Documentation
- Documented all 14 tables
- Added relationships and constraints
- Included business rules and valid values
- Created comprehensive schema overview

---

## 🔄 Polymorphic Queries

SQLAlchemy automatically handles polymorphic queries:

```python
# Automatically returns Student or Employer instance
user = User.query.filter_by(email='test@example.com').first()

# Check instance type
if isinstance(user, Student):
    print(user.grade)
elif isinstance(user, Employer):
    print(user.company_name)
```

---

## 💡 Best Practices

1. Always query through `User` base class for polymorphic loading
2. Use `db.session.get(User, uid)` for polymorphic ID lookups
3. Create wallet automatically on user registration
4. Validate domain/grade against VALID_DOMAINS/VALID_GRADES
5. Use transactions for financial operations (wallet + transaction records)

---

**End of Database Schema Documentation**
