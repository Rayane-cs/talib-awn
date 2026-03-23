# ══════════════════════════════════════════════════════════════════════════════
#  models_talib.py  —  Talib-Awn · طالب عون
#  SQLAlchemy models for MySQL.
#
#  Add to your app.py:
#    from models_talib import db   (or merge with existing models.py)
#
#  Then run:
#    flask db init && flask db migrate && flask db upgrade
#  OR:
#    with app.app_context(): db.create_all()
# ══════════════════════════════════════════════════════════════════════════════

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'users'

    id                = db.Column(db.Integer,     primary_key=True)
    email             = db.Column(db.String(120),  unique=True, nullable=False, index=True)
    password_hash     = db.Column(db.String(256),  nullable=False)
    firstname         = db.Column(db.String(80),   nullable=False)
    lastname          = db.Column(db.String(80),   nullable=False, default='')
    phone             = db.Column(db.String(30),   nullable=True)
    image             = db.Column(db.Text,         nullable=True)
    role              = db.Column(db.String(20),   nullable=False, default='client')
    grade             = db.Column(db.String(40),   nullable=False, default='Student')
    domain            = db.Column(db.String(80),   nullable=False, default='autre')

    # Student-specific
    institution       = db.Column(db.String(120),  nullable=True)
    field_of_study    = db.Column(db.String(120),  nullable=True)
    student_id_number = db.Column(db.String(60),   nullable=True)

    # Employer-specific
    company_name      = db.Column(db.String(120),  nullable=True)

    # Account state
    is_verified       = db.Column(db.Boolean,      default=True)
    is_banned         = db.Column(db.Boolean,      default=False)
    ban_reason        = db.Column(db.Text,         nullable=True)
    warnings          = db.Column(db.Integer,      default=0)

    created_at        = db.Column(db.DateTime,     default=datetime.utcnow)
    updated_at        = db.Column(db.DateTime,     default=datetime.utcnow,
                                                   onupdate=datetime.utcnow)


class Project(db.Model):
    __tablename__ = 'projects'

    id          = db.Column(db.Integer,  primary_key=True)
    title       = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text,     nullable=True)
    image       = db.Column(db.Text,     nullable=True)
    category    = db.Column(db.String(60), default='autre')
    status      = db.Column(db.String(30), default='open')
    owner_id    = db.Column(db.Integer,  db.ForeignKey('users.id'), nullable=False, index=True)
    is_visible  = db.Column(db.Boolean,  default=True)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)


class ProjectLike(db.Model):
    __tablename__ = 'project_likes'
    __table_args__ = (db.UniqueConstraint('project_id', 'user_id'),)

    id         = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), index=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id',    ondelete='CASCADE'), index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ProjectComment(db.Model):
    __tablename__ = 'project_comments'

    id         = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), index=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id',    ondelete='CASCADE'), index=True)
    content    = db.Column(db.Text,    nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Event(db.Model):
    __tablename__ = 'events'

    id         = db.Column(db.Integer, primary_key=True)
    title      = db.Column(db.String(200), nullable=False)
    description= db.Column(db.Text,     nullable=True)
    image      = db.Column(db.Text,     nullable=True)
    location   = db.Column(db.String(200), nullable=True)
    start_at   = db.Column(db.DateTime, nullable=True)
    end_at     = db.Column(db.DateTime, nullable=True)
    event_type = db.Column(db.String(40), default='other')
    capacity   = db.Column(db.Integer,  nullable=True)
    is_visible = db.Column(db.Boolean,  default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class EventRegistration(db.Model):
    __tablename__ = 'event_registrations'
    __table_args__ = (db.UniqueConstraint('event_id', 'user_id'),)

    id         = db.Column(db.Integer, primary_key=True)
    event_id   = db.Column(db.Integer, db.ForeignKey('events.id', ondelete='CASCADE'), index=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id',  ondelete='CASCADE'), index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Announcement(db.Model):
    __tablename__ = 'announcements'

    id         = db.Column(db.Integer,  primary_key=True)
    title      = db.Column(db.String(200), nullable=False, default='')
    content    = db.Column(db.Text,     nullable=False)
    image      = db.Column(db.Text,     nullable=True)
    is_pinned  = db.Column(db.Boolean,  default=False)
    is_visible = db.Column(db.Boolean,  default=True)
    author_id  = db.Column(db.Integer,  db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class UserFollow(db.Model):
    __tablename__ = 'user_follows'
    __table_args__ = (db.UniqueConstraint('follower_id', 'following_id'),)

    id           = db.Column(db.Integer, primary_key=True)
    follower_id  = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), index=True)
    following_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), index=True)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)


# ── Wallet / Payments ─────────────────────────────────────────────────────────

class Wallet(db.Model):
    __tablename__ = 'wallets'

    id         = db.Column(db.Integer,  primary_key=True)
    user_id    = db.Column(db.Integer,  db.ForeignKey('users.id'), unique=True, nullable=False)
    balance    = db.Column(db.Numeric(12, 2), default=0.0)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow,
                                        onupdate=datetime.utcnow)


class Transaction(db.Model):
    __tablename__ = 'transactions'

    id         = db.Column(db.Integer,  primary_key=True)
    user_id    = db.Column(db.Integer,  db.ForeignKey('users.id'), nullable=False, index=True)
    # type: deposit | escrow | release | refund | withdraw
    type       = db.Column(db.String(20), nullable=False)
    amount     = db.Column(db.Numeric(12, 2), nullable=False)
    # status: pending | completed | failed
    status     = db.Column(db.String(20), nullable=False, default='pending')
    reference  = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Escrow(db.Model):
    __tablename__ = 'escrows'

    id          = db.Column(db.Integer, primary_key=True)
    employer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    student_id  = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    amount      = db.Column(db.Numeric(12, 2), nullable=False)
    # status: held | released | cancelled
    status      = db.Column(db.String(20), nullable=False, default='held')
    job_id      = db.Column(db.Integer, nullable=True)
    note        = db.Column(db.Text,    nullable=True)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)


class Withdrawal(db.Model):
    __tablename__ = 'withdrawals'

    id             = db.Column(db.Integer,  primary_key=True)
    user_id        = db.Column(db.Integer,  db.ForeignKey('users.id'), nullable=False, index=True)
    amount         = db.Column(db.Numeric(12, 2), nullable=False)
    # payout_method: ccp | edahabia | baridimob
    payout_method  = db.Column(db.String(20), nullable=False, default='ccp')
    account_number = db.Column(db.String(120), nullable=False)
    # status: pending | approved | rejected
    status         = db.Column(db.String(20), nullable=False, default='pending')
    admin_note     = db.Column(db.Text, nullable=True)
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)
