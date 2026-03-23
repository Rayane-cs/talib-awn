# ══════════════════════════════════════════════════════════════════════════════
#  models.py  —  Talib-Awn · طالب عون
#  All SQLAlchemy models in one file.
#  Users table = shared identity base.
#  Students / Employers = role-specific tables (Joined Table Inheritance).
# ══════════════════════════════════════════════════════════════════════════════
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

db = SQLAlchemy()


def _now():
    """Return timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


# ── Base User (identity + auth only) ─────────────────────────────────────────

class User(db.Model):
    __tablename__ = 'users'

    id            = db.Column(db.Integer,     primary_key=True)
    type          = db.Column(db.String(20),  nullable=False, default='user')   # discriminator
    email         = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    firstname     = db.Column(db.String(80),  nullable=False)
    lastname      = db.Column(db.String(80),  nullable=False, default='')
    phone         = db.Column(db.String(30),  nullable=True)
    image         = db.Column(db.Text,        nullable=True)
    # Account state
    is_verified   = db.Column(db.Boolean,  default=True)
    is_banned     = db.Column(db.Boolean,  default=False)
    ban_reason    = db.Column(db.Text,     nullable=True)
    warnings      = db.Column(db.Integer,  default=0)
    created_at    = db.Column(db.DateTime, default=_now)
    updated_at    = db.Column(db.DateTime, default=_now, onupdate=_now)

    __mapper_args__ = {
        'polymorphic_identity': 'user',
        'polymorphic_on':       type,
    }


# ── Student profile ───────────────────────────────────────────────────────────

class Student(User):
    __tablename__ = 'students'

    id                = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    grade             = db.Column(db.String(40),  nullable=False, default='Student')
    domain            = db.Column(db.String(80),  nullable=False, default='autre')
    institution       = db.Column(db.String(120), nullable=True)
    field_of_study    = db.Column(db.String(120), nullable=True)
    student_id_number = db.Column(db.String(60),  nullable=True)

    __mapper_args__ = {
        'polymorphic_identity': 'student',
    }


# ── Employer profile ──────────────────────────────────────────────────────────

class Employer(User):
    __tablename__ = 'employers'

    id           = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    company_name = db.Column(db.String(120), nullable=True)
    domain       = db.Column(db.String(80),  nullable=False, default='autre')

    __mapper_args__ = {
        'polymorphic_identity': 'employer',
    }


# ─────────────────────────────────────────────────────────────────────────────
#  Remaining models — all FKs still point to users.id (unchanged)
# ─────────────────────────────────────────────────────────────────────────────

class Project(db.Model):
    __tablename__ = 'projects'
    id          = db.Column(db.Integer,     primary_key=True)
    title       = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text,        nullable=True)
    image       = db.Column(db.Text,        nullable=True)
    category    = db.Column(db.String(60),  default='autre')
    status      = db.Column(db.String(30),  default='open')
    owner_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    is_visible  = db.Column(db.Boolean,  default=True)
    created_at  = db.Column(db.DateTime, default=_now)


class ProjectLike(db.Model):
    __tablename__  = 'project_likes'
    __table_args__ = (db.UniqueConstraint('project_id', 'user_id'),)
    id         = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), index=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id',    ondelete='CASCADE'), index=True)
    created_at = db.Column(db.DateTime, default=_now)


class ProjectComment(db.Model):
    __tablename__ = 'project_comments'
    id         = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), index=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id',    ondelete='CASCADE'), index=True)
    content    = db.Column(db.Text,    nullable=False)
    created_at = db.Column(db.DateTime, default=_now)


class Event(db.Model):
    __tablename__ = 'events'
    id          = db.Column(db.Integer,     primary_key=True)
    title       = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text,        nullable=True)
    image       = db.Column(db.Text,        nullable=True)
    location    = db.Column(db.String(200), nullable=True)
    start_at    = db.Column(db.DateTime,    nullable=True)
    end_at      = db.Column(db.DateTime,    nullable=True)
    event_type  = db.Column(db.String(40),  default='other')
    capacity    = db.Column(db.Integer,     nullable=True)
    is_visible  = db.Column(db.Boolean,    default=True)
    created_at  = db.Column(db.DateTime,   default=_now)


class EventRegistration(db.Model):
    __tablename__  = 'event_registrations'
    __table_args__ = (db.UniqueConstraint('event_id', 'user_id'),)
    id         = db.Column(db.Integer, primary_key=True)
    event_id   = db.Column(db.Integer, db.ForeignKey('events.id', ondelete='CASCADE'), index=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id',  ondelete='CASCADE'), index=True)
    created_at = db.Column(db.DateTime, default=_now)


class Announcement(db.Model):
    __tablename__ = 'announcements'
    id         = db.Column(db.Integer,     primary_key=True)
    title      = db.Column(db.String(200), nullable=False, default='')
    content    = db.Column(db.Text,        nullable=False)
    image      = db.Column(db.Text,        nullable=True)
    is_pinned  = db.Column(db.Boolean,    default=False)
    is_visible = db.Column(db.Boolean,    default=True)
    author_id  = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime,   default=_now)


class UserFollow(db.Model):
    __tablename__  = 'user_follows'
    __table_args__ = (db.UniqueConstraint('follower_id', 'following_id'),)
    id           = db.Column(db.Integer, primary_key=True)
    follower_id  = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), index=True)
    following_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), index=True)
    created_at   = db.Column(db.DateTime, default=_now)


# ── Wallet / Payments ─────────────────────────────────────────────────────────

class Wallet(db.Model):
    __tablename__ = 'wallets'
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    balance    = db.Column(db.Numeric(12, 2), default=0.0)
    updated_at = db.Column(db.DateTime, default=_now, onupdate=_now)


class Transaction(db.Model):
    __tablename__ = 'transactions'
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    # type: deposit | escrow | release | refund | withdraw
    type       = db.Column(db.String(20), nullable=False)
    amount     = db.Column(db.Numeric(12, 2), nullable=False)
    # status: pending | completed | failed
    status     = db.Column(db.String(20), nullable=False, default='pending')
    reference  = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime,  default=_now)


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
    created_at  = db.Column(db.DateTime, default=_now)


class Withdrawal(db.Model):
    __tablename__ = 'withdrawals'
    id             = db.Column(db.Integer, primary_key=True)
    user_id        = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    amount         = db.Column(db.Numeric(12, 2), nullable=False)
    # payout_method: ccp | edahabia | baridimob
    payout_method  = db.Column(db.String(20), nullable=False, default='ccp')
    account_number = db.Column(db.String(120), nullable=False)
    # status: pending | approved | rejected
    status         = db.Column(db.String(20), nullable=False, default='pending')
    admin_note     = db.Column(db.Text, nullable=True)
    created_at     = db.Column(db.DateTime, default=_now)
