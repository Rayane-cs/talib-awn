from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'users'

    id         = db.Column(db.Integer, primary_key=True)
    identify   = db.Column(db.String(20), unique=True, nullable=False)
    firstname  = db.Column(db.String(80), nullable=False)
    lastname   = db.Column(db.String(80), nullable=False)
    email      = db.Column(db.String(120), unique=True, nullable=False)
    phone      = db.Column(db.String(20), unique=True, nullable=False)
    password   = db.Column(db.String(256), nullable=False)
    image      = db.Column(db.String(512), nullable=True)
    role       = db.Column(db.String(20), nullable=False, default='client')
    grade      = db.Column(db.String(60), nullable=True)
    domain     = db.Column(db.String(80), nullable=True)
    is_banned  = db.Column(db.Boolean, default=False, nullable=False)
    ban_reason = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owned_projects = db.relationship(
        'Project',
        backref='owner',
        lazy='dynamic',
        foreign_keys='Project.owner_id',
        cascade='all, delete-orphan',
    )
    announcements = db.relationship(
        'Announcement',
        backref='author',
        lazy='dynamic',
        foreign_keys='Announcement.author_id',
        cascade='all, delete-orphan',
    )
    event_registrations = db.relationship(
        'EventRegistration',
        backref='user',
        lazy='dynamic',
        cascade='all, delete-orphan',
    )
    project_likes = db.relationship(
        'ProjectLike',
        backref='user',
        lazy='dynamic',
        cascade='all, delete-orphan',
    )
    project_comments = db.relationship(
        'ProjectComment',
        backref='user',
        lazy='dynamic',
        cascade='all, delete-orphan',
    )
    followers = db.relationship(
        'UserFollow',
        foreign_keys='UserFollow.following_id',
        backref=db.backref('following', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan',
    )
    following = db.relationship(
        'UserFollow',
        foreign_keys='UserFollow.follower_id',
        backref=db.backref('follower', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan',
    )

    def __repr__(self):
        return f'<User {self.email} role={self.role}>'


class Event(db.Model):
    __tablename__ = 'events'

    id          = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    location    = db.Column(db.String(200), nullable=True)
    image       = db.Column(db.String(512), nullable=True)
    start_at    = db.Column(db.DateTime, nullable=False)
    end_at      = db.Column(db.DateTime, nullable=True)
    event_type  = db.Column(db.String(50), default='other', nullable=False)
    capacity    = db.Column(db.Integer, nullable=True)
    is_visible  = db.Column(db.Boolean, default=True, nullable=False)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at  = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    registrations = db.relationship(
        'EventRegistration',
        backref='event',
        lazy='dynamic',
        cascade='all, delete-orphan',
    )

    @property
    def registered_count(self):
        return self.registrations.count()

    @property
    def is_full(self):
        if self.capacity is None:
            return False
        return self.registered_count >= self.capacity

    def __repr__(self):
        return f'<Event {self.title}>'


class EventRegistration(db.Model):
    __tablename__ = 'event_registrations'

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    event_id   = db.Column(db.Integer, db.ForeignKey('events.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'event_id', name='uq_user_event'),
    )

    def __repr__(self):
        return f'<EventRegistration user={self.user_id} event={self.event_id}>'


class Announcement(db.Model):
    __tablename__ = 'announcements'

    id         = db.Column(db.Integer, primary_key=True)
    title      = db.Column(db.String(200), nullable=False)
    content    = db.Column(db.Text, nullable=False)
    image      = db.Column(db.String(512), nullable=True)
    is_pinned  = db.Column(db.Boolean, default=False, nullable=False)
    is_visible = db.Column(db.Boolean, default=True, nullable=False)
    author_id  = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Announcement {self.title}>'


class Project(db.Model):
    __tablename__ = 'projects'

    id          = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    image       = db.Column(db.String(512), nullable=True)
    category    = db.Column(db.String(80), default='other', nullable=False)
    status      = db.Column(db.String(40), default='open', nullable=False)
    is_visible  = db.Column(db.Boolean, default=True, nullable=False)
    owner_id    = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at  = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    likes = db.relationship(
        'ProjectLike',
        backref='project',
        lazy='dynamic',
        cascade='all, delete-orphan',
    )
    comments = db.relationship(
        'ProjectComment',
        backref='project',
        lazy='dynamic',
        cascade='all, delete-orphan',
    )

    @property
    def like_count(self):
        return self.likes.count()

    @property
    def comment_count(self):
        return self.comments.count()

    def __repr__(self):
        return f'<Project {self.title}>'


class ProjectLike(db.Model):
    __tablename__ = 'project_likes'

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'project_id', name='uq_user_project_like'),
    )

    def __repr__(self):
        return f'<ProjectLike user={self.user_id} project={self.project_id}>'


class ProjectComment(db.Model):
    __tablename__ = 'project_comments'

    id         = db.Column(db.Integer, primary_key=True)
    content    = db.Column(db.Text, nullable=False)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<ProjectComment id={self.id}>'


class UserFollow(db.Model):
    __tablename__ = 'user_follows'

    id           = db.Column(db.Integer, primary_key=True)
    follower_id  = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    following_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('follower_id', 'following_id', name='uq_follow_pair'),
        db.CheckConstraint('follower_id != following_id', name='no_self_follow'),
    )

    def __repr__(self):
        return f'<UserFollow {self.follower_id} -> {self.following_id}>'
