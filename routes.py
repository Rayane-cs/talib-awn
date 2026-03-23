# ══════════════════════════════════════════════════════════════════════════════
#  routes.py  —  Talib-Awn · طالب عون
#  All Flask routes in one Blueprint.
#  Covers: Auth, Profile, Social, Projects, Events, Announcements,
#          Wallet, Escrow, Withdrawals, Admin.
# ══════════════════════════════════════════════════════════════════════════════

import os, random, string, time
from datetime import datetime, timedelta

from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from flask_jwt_extended import (
    jwt_required, create_access_token, create_refresh_token,
    get_jwt_identity, verify_jwt_in_request,
)
from werkzeug.security import check_password_hash, generate_password_hash

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from models import (
    db, User, Student, Employer,
    Project, ProjectLike, ProjectComment,
    Event, EventRegistration, Announcement, UserFollow,
    Wallet, Transaction, Escrow, Withdrawal,
)
from parsers import get_json, require_fields, str_field, float_field, int_field, bool_field

bp = Blueprint('api', __name__)

# ─────────────────────────────────────────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────────────────────────────────────────
GMAIL_ADDRESS  = os.environ.get('GMAIL_ADDRESS',  'universitychlefclub@gmail.com')
GMAIL_APP_PASS = os.environ.get('GMAIL_APP_PASS', '')
PLATFORM_NAME  = 'طالب-عون (Talib-Awn)'
OTP_EXPIRY_SEC = 120

VALID_GRADES  = ['Student', 'Professor', 'Researcher', 'Company manager']
VALID_DOMAINS = [
    'intelligence artificielle', 'developpement web', 'cyber securite',
    'reseaux et telecommunications', 'systemes embarques',
    'science des donnees', 'genie logiciel', 'autre',
]

# In-memory OTP stores  { email: { otp, sent_at, data/verified } }
_pending_registrations: dict = {}
_pending_resets:         dict = {}
_pending_logins:         dict = {}


# ═════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ═════════════════════════════════════════════════════════════════════════════

def _otp() -> str:
    return ''.join(random.choices(string.digits, k=8))

def _ok(data=None, **kw):
    r = {'ok': True}
    if data is not None: r['data'] = data
    r.update(kw)
    return jsonify(r), 200

def _created(data=None, **kw):
    r = {'ok': True}
    if data is not None: r['data'] = data
    r.update(kw)
    return jsonify(r), 201

def _err(msg, code=400):
    return jsonify({'ok': False, 'error': msg}), code

def _current_user():
    try:
        verify_jwt_in_request()
        uid = get_jwt_identity()
        # polymorphic load: returns Student or Employer instance automatically
        return db.session.get(User, uid)
    except Exception:
        return None

def _user_dict(u: User) -> dict:
    base = {
        'id': u.id, 'type': u.type,
        'firstname': u.firstname, 'lastname': u.lastname,
        'email': u.email, 'phone': u.phone, 'image': u.image,
        'is_banned': u.is_banned, 'ban_reason': u.ban_reason,
        'warnings': u.warnings or 0, 'is_verified': u.is_verified,
        'created_at': u.created_at.isoformat() if u.created_at else None,
    }
    if isinstance(u, Student):
        base.update({
            'role': 'student',
            'grade': u.grade, 'domain': u.domain,
            'institution': u.institution,
            'field_of_study': u.field_of_study,
            'student_id_number': u.student_id_number,
        })
    elif isinstance(u, Employer):
        base.update({
            'role': 'employer',
            'company_name': u.company_name,
            'domain': u.domain,
        })
    return base

def _send_email(to: str, subject: str, html: str):
    msg = MIMEMultipart('alternative')
    msg['From']    = f'{PLATFORM_NAME} <{GMAIL_ADDRESS}>'
    msg['To']      = to
    msg['Subject'] = subject
    msg.attach(MIMEText(html, 'html'))
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
        s.login(GMAIL_ADDRESS, GMAIL_APP_PASS)
        s.sendmail(GMAIL_ADDRESS, to, msg.as_string())

def _otp_html(otp: str) -> str:
    cells = ''.join(
        f'<td style="padding:0 4px;"><div style="width:50px;height:62px;'
        f'background:#fff;border:2px solid #7C3AED;border-radius:10px;'
        f'font-family:monospace;font-size:30px;font-weight:700;color:#5B21B6;'
        f'text-align:center;line-height:62px;">{c}</div></td>'
        for c in otp
    )
    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8"/></head>
<body style="margin:0;padding:0;background:#F5F3FF;font-family:Cairo,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#F5F3FF;padding:40px 16px;">
<tr><td align="center">
<table width="520" cellpadding="0" cellspacing="0"
       style="background:#fff;border-radius:20px;overflow:hidden;box-shadow:0 8px 40px rgba(26,10,46,0.10);">
  <tr><td style="background:linear-gradient(135deg,#3B0F8C,#7C3AED);padding:44px;text-align:center;">
    <h1 style="margin:0;color:#fff;font-size:26px;font-weight:700;">{PLATFORM_NAME}</h1>
    <p style="margin:10px 0 0;color:rgba(255,255,255,0.7);font-size:13px;">Verify Your Identity</p>
  </td></tr>
  <tr><td style="padding:48px;text-align:center;">
    <p style="font-family:sans-serif;font-size:15px;color:#555;margin:0 0 28px;line-height:1.7;">
      Use the code below to complete your verification.<br/>
      Expires in <strong style="color:#5B21B6;">{OTP_EXPIRY_SEC // 60} minutes</strong>.
    </p>
    <div style="background:#F5F3FF;border:2px dashed #7C3AED;border-radius:16px;padding:32px 24px;margin:0 0 28px;">
      <p style="margin:0 0 16px;font-size:11px;letter-spacing:0.15em;text-transform:uppercase;color:#999;">Your OTP Code</p>
      <table cellpadding="0" cellspacing="0" border="0" style="margin:0 auto;"><tr>{cells}</tr></table>
    </div>
    <div style="background:#FEF3C7;border:1px solid #D97706;border-radius:10px;padding:12px 20px;margin-bottom:28px;">
      <p style="margin:0;font-family:sans-serif;font-size:12px;color:#92400E;">
        ⏰ Expires in {OTP_EXPIRY_SEC // 60} minutes. Do not share this code.
      </p>
    </div>
  </td></tr>
  <tr><td style="background:#F5F3FF;padding:24px;text-align:center;border-top:1px solid #EDE9FE;">
    <p style="font-family:sans-serif;font-size:11px;color:#bbb;margin:0;">© 2026 {PLATFORM_NAME} · Algeria</p>
  </td></tr>
</table></td></tr></table></body></html>"""


# ═════════════════════════════════════════════════════════════════════════════
#  AUTH — REGISTER
# ═════════════════════════════════════════════════════════════════════════════

@bp.post('/auth/register/send-otp')
def register_send_otp():
    """Step 1 — validate + send OTP email."""
    d = get_json()
    email      = str_field(d, 'email').lower()
    password   = str_field(d, 'password')
    firstname  = str_field(d, 'firstname')
    lastname   = str_field(d, 'lastname')
    user_type  = str_field(d, 'type', 'student').lower()   # 'student' | 'employer'
    grade      = str_field(d, 'grade', 'Student')
    domain     = str_field(d, 'domain', 'autre').lower()
    phone      = str_field(d, 'phone')

    if user_type not in ('student', 'employer'): user_type = 'student'
    if not email or '@' not in email: return _err('Valid email required.')
    if len(password) < 6:             return _err('Password must be at least 6 characters.')
    if not firstname:                 return _err('First name required.')
    if user_type == 'student' and grade not in VALID_GRADES:
        return _err(f'Grade must be one of: {", ".join(VALID_GRADES)}')
    if domain not in VALID_DOMAINS:   domain = 'autre'
    if User.query.filter_by(email=email).first():
        return _err('An account with this email already exists.', 409)

    otp = _otp()
    _pending_registrations[email] = {
        'otp': otp, 'sent_at': time.time(),
        'data': {
            'type':              user_type,
            'email':             email,
            'password_hash':     generate_password_hash(password),
            'firstname':         firstname,
            'lastname':          lastname,
            'grade':             grade,
            'domain':            domain,
            'phone':             phone,
            'institution':       str_field(d, 'institution'),
            'field_of_study':    str_field(d, 'field_of_study'),
            'student_id_number': str_field(d, 'student_id_number'),
            'company_name':      str_field(d, 'company_name'),
        }
    }
    try:
        _send_email(email, f'Your Verification Code — {PLATFORM_NAME}', _otp_html(otp))
    except Exception as e:
        return _err(f'Failed to send email: {e}')
    return _ok(message='OTP sent to your email.')


@bp.post('/auth/register/verify-otp')
def register_verify_otp():
    """Step 2 — verify OTP, create user + wallet, return JWT."""
    d     = get_json()
    email = str_field(d, 'email').lower()
    otp   = str_field(d, 'otp')

    p = _pending_registrations.get(email)
    if not p:
        return _err('No pending registration. Please start again.')
    if time.time() - p['sent_at'] > OTP_EXPIRY_SEC:
        _pending_registrations.pop(email, None)
        return _err('OTP expired. Please request a new one.')
    if p['otp'] != otp:
        return _err('Incorrect OTP.')

    reg = p['data']
    _pending_registrations.pop(email, None)

    if User.query.filter_by(email=email).first():
        return _err('Account already exists.', 409)

    common = dict(
        email=reg['email'], password_hash=reg['password_hash'],
        firstname=reg['firstname'], lastname=reg['lastname'],
        phone=reg['phone'], is_verified=True, is_banned=False, warnings=0,
    )
    if reg['type'] == 'employer':
        user = Employer(
            **common,
            company_name=reg['company_name'],
            domain=reg['domain'],
        )
    else:
        user = Student(
            **common,
            grade=reg['grade'], domain=reg['domain'],
            institution=reg['institution'],
            field_of_study=reg['field_of_study'],
            student_id_number=reg['student_id_number'],
        )
    db.session.add(user)
    db.session.flush()
    db.session.add(Wallet(user_id=user.id, balance=0.0))
    db.session.commit()

    access  = create_access_token(identity=user.id,  expires_delta=timedelta(days=7))
    refresh = create_refresh_token(identity=user.id, expires_delta=timedelta(days=30))
    return jsonify({'ok': True, 'data': {
        'user': _user_dict(user), 'access_token': access, 'refresh_token': refresh,
    }}), 201


# ═════════════════════════════════════════════════════════════════════════════
#  AUTH — LOGIN / REFRESH / ME
# ═════════════════════════════════════════════════════════════════════════════

@bp.post('/auth/login')
def login():
    d        = get_json()
    email    = str_field(d, 'email').lower()
    password = str_field(d, 'password')

    # polymorphic query — finds Student or Employer automatically
    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        return _err('Invalid email or password.', 401)
    if user.is_banned:
        return _err(f'Account suspended. Reason: {user.ban_reason}', 403)

    access  = create_access_token(identity=user.id,  expires_delta=timedelta(days=7))
    refresh = create_refresh_token(identity=user.id, expires_delta=timedelta(days=30))
    return _ok({'user': _user_dict(user), 'access_token': access, 'refresh_token': refresh})


@bp.post('/auth/login/send-otp')
def login_send_otp():
    """Send OTP for passwordless login."""
    d = get_json()
    contact = str_field(d, 'contact').lower()
    type_ = str_field(d, 'type')
    user = User.query.filter_by(email=contact).first() if type_ == 'email' else User.query.filter_by(phone=contact).first()  # polymorphic
    if not user: return _err('User not found.', 404)
    if user.is_banned: return _err(f'Account suspended. Reason: {user.ban_reason}', 403)
    otp = _otp()
    _pending_logins[contact] = {'otp': otp, 'sent_at': time.time(), 'user_id': user.id}
    if type_ == 'email':
        try: _send_email(contact, f'Login Code — {PLATFORM_NAME}', _otp_html(otp))
        except Exception as e: return _err(f'Failed to send email: {e}')
    # No actual SMS integration natively, we just pretend it succeeds.
    return _ok(message='OTP sent.')


@bp.post('/auth/login/verify-otp')
def login_verify_otp():
    """Verify OTP and return JWT for passwordless login."""
    d = get_json()
    contact = str_field(d, 'contact').lower()
    otp = str_field(d, 'token')
    p = _pending_logins.get(contact)
    if not p: return _err('No pending login.')
    if time.time() - p['sent_at'] > OTP_EXPIRY_SEC:
        _pending_logins.pop(contact, None); return _err('OTP expired.')
    if p['otp'] != otp: return _err('Incorrect OTP.')
    user = db.session.get(User, p['user_id'])
    _pending_logins.pop(contact, None)
    if user.is_banned: return _err('Account suspended.', 403)
    access = create_access_token(identity=user.id, expires_delta=timedelta(days=7))
    refresh = create_refresh_token(identity=user.id, expires_delta=timedelta(days=30))
    return _ok({'user': _user_dict(user), 'access_token': access, 'refresh_token': refresh})


@bp.post('/auth/refresh')
@jwt_required(refresh=True)
def refresh_token():
    uid    = get_jwt_identity()
    access = create_access_token(identity=uid, expires_delta=timedelta(days=7))
    return _ok({'access_token': access})


@bp.get('/auth/me')
@jwt_required()
def get_me():
    user = _current_user()
    if not user: return _err('User not found.', 404)
    return _ok(_user_dict(user))


# ═════════════════════════════════════════════════════════════════════════════
#  AUTH — PASSWORD RESET
# ═════════════════════════════════════════════════════════════════════════════

@bp.post('/auth/reset/send-otp')
def reset_send_otp():
    email = str_field(get_json(), 'email').lower()
    # Always return OK (don't reveal if email exists)
    user  = User.query.filter_by(email=email).first()  # polymorphic
    if user:
        otp = _otp()
        _pending_resets[email] = {'otp': otp, 'sent_at': time.time(), 'verified': False}
        try:
            _send_email(email, f'Password Reset — {PLATFORM_NAME}', _otp_html(otp))
        except Exception as e:
            return _err(f'Failed to send email: {e}')
    return _ok(message='If that email exists, an OTP was sent.')


@bp.post('/auth/reset/verify-otp')
def reset_verify_otp():
    d     = get_json()
    email = str_field(d, 'email').lower()
    otp   = str_field(d, 'otp')
    p = _pending_resets.get(email)
    if not p:                                    return _err('No reset pending.')
    if time.time() - p['sent_at'] > OTP_EXPIRY_SEC:
        _pending_resets.pop(email, None);        return _err('OTP expired.')
    if p['otp'] != otp:                          return _err('Incorrect OTP.')
    _pending_resets[email]['verified'] = True
    return _ok(message='OTP verified.')


@bp.post('/auth/reset/set-password')
def reset_set_password():
    d            = get_json()
    email        = str_field(d, 'email').lower()
    otp          = str_field(d, 'otp')
    new_password = str_field(d, 'new_password')
    p = _pending_resets.get(email)
    if not p or not p.get('verified'): return _err('OTP not verified.')
    if p['otp'] != otp:                return _err('OTP mismatch.')
    if len(new_password) < 6:          return _err('Password too short (min 6 chars).')
    user = User.query.filter_by(email=email).first()  # polymorphic
    if not user:                       return _err('User not found.', 404)
    user.password_hash = generate_password_hash(new_password)
    db.session.commit()
    _pending_resets.pop(email, None)
    return _ok(message='Password updated successfully.')


# ═════════════════════════════════════════════════════════════════════════════
#  PROFILE
# ═════════════════════════════════════════════════════════════════════════════

@bp.patch('/users/me')
@jwt_required()
def update_profile():
    user = _current_user()
    if not user: return _err('Not found.', 404)
    d = get_json()
    for f in ['firstname', 'lastname', 'phone', 'image', 'domain',
              'institution', 'field_of_study', 'student_id_number', 'company_name']:
        if f in d: setattr(user, f, d[f])
    db.session.commit()
    return _ok(_user_dict(user))


@bp.patch('/users/me/password')
@jwt_required()
def change_password():
    user = _current_user()
    if not user: return _err('Not found.', 404)
    d = get_json()
    if not check_password_hash(user.password_hash, str_field(d, 'current_password')):
        return _err('Current password is incorrect.', 401)
    new_pw = str_field(d, 'new_password')
    if len(new_pw) < 6: return _err('New password too short.')
    user.password_hash = generate_password_hash(new_pw)
    db.session.commit()
    return _ok(message='Password changed.')


@bp.get('/users/<int:uid>')
@jwt_required(optional=True)
def get_user_info(uid):
    me   = _current_user()
    user = db.session.get(User, uid)  # polymorphic
    if not user: return _err('User not found.', 404)

    projects       = Project.query.filter_by(owner_id=uid, is_visible=True).order_by(Project.created_at.desc()).all()
    followers_count = UserFollow.query.filter_by(following_id=uid).count()
    following_count = UserFollow.query.filter_by(follower_id=uid).count()
    is_following    = bool(me and UserFollow.query.filter_by(follower_id=me.id, following_id=uid).first())

    info = _user_dict(user)
    info.update({'followers_count': followers_count, 'following_count': following_count, 'is_following': is_following})
    return _ok({'user': info, 'projects': [_proj_dict(p, me.id if me else None) for p in projects]})


@bp.get('/users/search')
@jwt_required(optional=True)
def search_users():
    q = (request.args.get('q') or '').strip()
    users = User.query.filter(
        (User.firstname.ilike(f'%{q}%')) | (User.lastname.ilike(f'%{q}%'))
    ).limit(20).all()
    return _ok([_user_dict(u) for u in users])


# ═════════════════════════════════════════════════════════════════════════════
#  SOCIAL — FOLLOW
# ═════════════════════════════════════════════════════════════════════════════

@bp.post('/users/<int:uid>/follow')
@jwt_required()
def toggle_follow(uid):
    me = _current_user()
    if not me:     return _err('Not authenticated.', 401)
    if me.id == uid: return _err('Cannot follow yourself.')
    existing = UserFollow.query.filter_by(follower_id=me.id, following_id=uid).first()
    if existing:
        db.session.delete(existing); db.session.commit()
        return _ok({'following': False})
    db.session.add(UserFollow(follower_id=me.id, following_id=uid))
    db.session.commit()
    # Best-effort follow notification email
    try:
        target = User.query.get(uid)
        if target and target.email:
            _send_follow_email(me, target)
    except Exception:
        pass
    return _ok({'following': True})


def _send_follow_email(follower: User, target: User):
    name = f'{follower.firstname} {follower.lastname}'.strip()
    html = f"""<html><body style="font-family:Cairo,sans-serif;background:#F5F3FF;padding:32px;">
<div style="max-width:480px;margin:0 auto;background:#fff;border-radius:18px;
            box-shadow:0 8px 32px rgba(26,10,46,0.1);overflow:hidden;">
  <div style="background:linear-gradient(135deg,#3B0F8C,#7C3AED);padding:36px;text-align:center;">
    <h1 style="color:#fff;margin:0;font-size:22px;">You have a new follower!</h1>
  </div>
  <div style="padding:36px;text-align:center;">
    <p style="font-size:15px;color:#444;line-height:1.8;">
      <strong style="color:#5B21B6;">{name}</strong> started following you on {PLATFORM_NAME}.
    </p>
  </div>
</div></body></html>"""
    _send_email(target.email, f'{name} started following you — {PLATFORM_NAME}', html)


# ═════════════════════════════════════════════════════════════════════════════
#  PROJECTS
# ═════════════════════════════════════════════════════════════════════════════

def _proj_dict(p: Project, me_id=None) -> dict:
    owner = User.query.get(p.owner_id)
    return {
        'id': p.id, 'title': p.title, 'description': p.description,
        'image': p.image, 'category': p.category, 'status': p.status,
        'owner_id': p.owner_id,
        'created_at': p.created_at.isoformat() if p.created_at else None,
        'like_count':    ProjectLike.query.filter_by(project_id=p.id).count(),
        'comment_count': ProjectComment.query.filter_by(project_id=p.id).count(),
        'is_liked': bool(me_id and ProjectLike.query.filter_by(project_id=p.id, user_id=me_id).first()),
        'owner': {'id': owner.id, 'firstname': owner.firstname, 'lastname': owner.lastname,
                  'image': owner.image, 'grade': owner.grade, 'domain': owner.domain} if owner else None,
    }


@bp.get('/projects')
@jwt_required(optional=True)
def get_projects():
    me       = _current_user()
    category = request.args.get('category')
    q = Project.query.filter_by(is_visible=True).order_by(Project.created_at.desc())
    if category and category != 'all': q = q.filter_by(category=category)
    return _ok([_proj_dict(p, me.id if me else None) for p in q.all()])


@bp.post('/projects')
@jwt_required()
def create_project():
    me = _current_user()
    if not me: return _err('Not authenticated.', 401)
    d  = get_json()
    p  = Project(title=str_field(d,'title'), description=str_field(d,'description'),
                 image=d.get('image'), category=str_field(d,'category','autre'),
                 status=str_field(d,'status','open'), owner_id=me.id, is_visible=True)
    db.session.add(p); db.session.commit()
    return _created(_proj_dict(p, me.id))


@bp.patch('/projects/<int:pid>')
@jwt_required()
def update_project(pid):
    me = _current_user(); p = Project.query.get(pid)
    if not p: return _err('Not found.', 404)
    if p.owner_id != me.id and me.type != 'admin': return _err('Forbidden.', 403)
    d = get_json()
    for f in ['title', 'description', 'image', 'category', 'status']:
        if f in d: setattr(p, f, d[f])
    db.session.commit()
    return _ok(_proj_dict(p, me.id))


@bp.delete('/projects/<int:pid>')
@jwt_required()
def delete_project(pid):
    me = _current_user(); p = Project.query.get(pid)
    if not p: return _err('Not found.', 404)
    if p.owner_id != me.id and me.type != 'admin': return _err('Forbidden.', 403)
    db.session.delete(p); db.session.commit()
    return _ok(message='Deleted.')


@bp.post('/projects/<int:pid>/like')
@jwt_required()
def toggle_like(pid):
    me = _current_user()
    existing = ProjectLike.query.filter_by(project_id=pid, user_id=me.id).first()
    if existing:
        db.session.delete(existing); db.session.commit(); return _ok({'liked': False})
    db.session.add(ProjectLike(project_id=pid, user_id=me.id))
    db.session.commit()
    return _ok({'liked': True})


@bp.get('/projects/<int:pid>/comments')
@jwt_required(optional=True)
def get_comments(pid):
    def c_dict(c):
        u = User.query.get(c.user_id)
        return {'id': c.id, 'content': c.content, 'user_id': c.user_id,
                'created_at': c.created_at.isoformat() if c.created_at else None,
                'user': {'id': u.id, 'firstname': u.firstname, 'lastname': u.lastname, 'image': u.image} if u else None}
    return _ok([c_dict(c) for c in ProjectComment.query.filter_by(project_id=pid)
                .order_by(ProjectComment.created_at.asc()).all()])


@bp.post('/projects/<int:pid>/comments')
@jwt_required()
def add_comment(pid):
    me = _current_user()
    c  = ProjectComment(project_id=pid, user_id=me.id, content=str_field(get_json(), 'content'))
    db.session.add(c); db.session.commit()
    return _created({'id': c.id, 'content': c.content, 'user_id': c.user_id,
                     'created_at': c.created_at.isoformat() if c.created_at else None,
                     'user': {'id': me.id, 'firstname': me.firstname,
                              'lastname': me.lastname, 'image': me.image}})


@bp.delete('/comments/<int:cid>')
@jwt_required()
def delete_comment(cid):
    me = _current_user(); c = ProjectComment.query.get(cid)
    if not c: return _err('Not found.', 404)
    if c.user_id != me.id and me.type != 'admin': return _err('Forbidden.', 403)
    db.session.delete(c); db.session.commit()
    return _ok(message='Deleted.')


# ═════════════════════════════════════════════════════════════════════════════
#  EVENTS
# ═════════════════════════════════════════════════════════════════════════════

def _event_dict(e: Event, me_id=None) -> dict:
    return {
        'id': e.id, 'title': e.title, 'description': e.description,
        'image': e.image, 'location': e.location, 'event_type': e.event_type,
        'capacity': e.capacity, 'is_visible': e.is_visible,
        'start_at': e.start_at.isoformat() if e.start_at else None,
        'end_at':   e.end_at.isoformat()   if e.end_at   else None,
        'created_at': e.created_at.isoformat() if e.created_at else None,
        'registration_count': EventRegistration.query.filter_by(event_id=e.id).count(),
        'is_registered': bool(me_id and EventRegistration.query.filter_by(event_id=e.id, user_id=me_id).first()),
    }


@bp.get('/events')
@jwt_required(optional=True)
def get_events():
    me = _current_user()
    events = Event.query.filter_by(is_visible=True).order_by(Event.start_at.asc()).all()
    return _ok([_event_dict(e, me.id if me else None) for e in events])


@bp.post('/events/<int:eid>/register')
@jwt_required()
def join_event(eid):
    me = _current_user()
    if EventRegistration.query.filter_by(event_id=eid, user_id=me.id).first():
        return _err('Already registered.', 409)
    db.session.add(EventRegistration(event_id=eid, user_id=me.id))
    db.session.commit()
    return _ok(message='Registered.')


@bp.delete('/events/<int:eid>/register')
@jwt_required()
def quit_event(eid):
    me  = _current_user()
    reg = EventRegistration.query.filter_by(event_id=eid, user_id=me.id).first()
    if not reg: return _err('Not registered.', 404)
    db.session.delete(reg); db.session.commit()
    return _ok(message='Unregistered.')


# ═════════════════════════════════════════════════════════════════════════════
#  ANNOUNCEMENTS
# ═════════════════════════════════════════════════════════════════════════════

def _ann_dict(a: Announcement) -> dict:
    author = User.query.get(a.author_id) if a.author_id else None
    return {
        'id': a.id, 'title': a.title, 'content': a.content, 'image': a.image,
        'is_pinned': a.is_pinned, 'is_visible': a.is_visible,
        'created_at': a.created_at.isoformat() if a.created_at else None,
        'author': {'firstname': author.firstname, 'lastname': author.lastname,
                   'image': author.image} if author else None,
    }


@bp.get('/announcements')
@jwt_required(optional=True)
def get_announcements():
    anns = Announcement.query.filter_by(is_visible=True)\
        .order_by(Announcement.is_pinned.desc(), Announcement.created_at.desc()).all()
    return _ok([_ann_dict(a) for a in anns])


# ═════════════════════════════════════════════════════════════════════════════
#  STATS
# ═════════════════════════════════════════════════════════════════════════════

@bp.get('/stats')
def get_stats():
    return _ok({
        'projects':  Project.query.filter_by(is_visible=True).count(),
        'events':    Event.query.filter_by(is_visible=True).count(),
        'students':  Student.query.count(),
        'employers': Employer.query.count(),
        'users':     Student.query.count() + Employer.query.count(),
    })


# ═════════════════════════════════════════════════════════════════════════════
#  WALLET
# ═════════════════════════════════════════════════════════════════════════════

def _wallet_dict(w: Wallet) -> dict:
    return {'user_id': w.user_id, 'balance': float(w.balance),
            'updated_at': w.updated_at.isoformat() if w.updated_at else None}

def _tx_dict(t: Transaction) -> dict:
    return {'id': t.id, 'user_id': t.user_id, 'type': t.type,
            'amount': float(t.amount), 'status': t.status, 'reference': t.reference,
            'created_at': t.created_at.isoformat() if t.created_at else None}


@bp.get('/wallet')
@jwt_required()
def get_wallet():
    me = _current_user()
    w  = Wallet.query.filter_by(user_id=me.id).first()
    if not w:
        w = Wallet(user_id=me.id, balance=0.0); db.session.add(w); db.session.commit()
    return _ok(_wallet_dict(w))


@bp.get('/wallet/transactions')
@jwt_required()
def get_transactions():
    me    = _current_user()
    limit = min(int(request.args.get('limit', 50)), 200)
    txs   = Transaction.query.filter_by(user_id=me.id)\
        .order_by(Transaction.created_at.desc()).limit(limit).all()
    return _ok([_tx_dict(t) for t in txs])


@bp.post('/wallet/deposit')
@jwt_required()
def request_deposit():
    """Manual deposit request (admin confirms later)."""
    me = _current_user()
    d  = get_json()
    amount = float_field(d, 'amount')
    if amount < 100:    return _err('Minimum deposit is 100 DZD.')
    if amount > 200000: return _err('Maximum deposit is 200,000 DZD.')
    import random, string as _s
    tx = Transaction(user_id=me.id, type='deposit', amount=amount,
                     status='pending', reference='manual-' + ''.join(random.choices(_s.digits, k=8)))
    db.session.add(tx); db.session.commit()
    return _created(_tx_dict(tx))


@bp.post('/webhook/chargily')
def chargily_webhook():
    """Called by Chargily after successful payment."""
    payload = request.get_json(silent=True) or {}
    if payload.get('status') != 'paid': return jsonify({'ok': True}), 200
    meta    = payload.get('metadata', {})
    user_id = meta.get('user_id')
    amount  = float(payload.get('amount', 0))
    ref     = payload.get('id', '')
    if not user_id or amount <= 0: return jsonify({'ok': False, 'error': 'bad payload'}), 400
    if Transaction.query.filter_by(reference=ref, status='completed').first():
        return jsonify({'ok': True}), 200
    wallet = Wallet.query.filter_by(user_id=user_id).first()
    if not wallet:
        wallet = Wallet(user_id=user_id, balance=0.0); db.session.add(wallet)
    wallet.balance += amount; wallet.updated_at = datetime.utcnow()
    db.session.add(Transaction(user_id=user_id, type='deposit', amount=amount, status='completed', reference=ref))
    db.session.commit()
    return jsonify({'ok': True}), 200


# ═════════════════════════════════════════════════════════════════════════════
#  ESCROW
# ═════════════════════════════════════════════════════════════════════════════

def _escrow_dict(e: Escrow) -> dict:
    student  = User.query.get(e.student_id)
    employer = User.query.get(e.employer_id)
    def mini(u): return {'id': u.id, 'firstname': u.firstname, 'lastname': u.lastname, 'image': u.image} if u else None
    return {'id': e.id, 'employer_id': e.employer_id, 'student_id': e.student_id,
            'amount': float(e.amount), 'status': e.status, 'note': e.note, 'job_id': e.job_id,
            'created_at': e.created_at.isoformat() if e.created_at else None,
            'student': mini(student), 'employer': mini(employer)}


@bp.post('/escrow')
@jwt_required()
def create_escrow():
    me = _current_user(); d = get_json()
    amount     = float_field(d, 'amount')
    student_id = int_field(d, 'student_id')
    if not student_id: return _err('student_id required.')
    if amount <= 0:    return _err('amount must be positive.')
    wallet = Wallet.query.filter_by(user_id=me.id).first()
    if not wallet or float(wallet.balance) < amount: return _err('Insufficient balance.')
    wallet.balance -= amount; wallet.updated_at = datetime.utcnow()
    escrow = Escrow(employer_id=me.id, student_id=student_id, amount=amount,
                    status='held', job_id=d.get('job_id'), note=d.get('note'))
    db.session.add(escrow)
    db.session.add(Transaction(user_id=me.id, type='escrow', amount=amount, status='completed'))
    db.session.commit()
    return _created(_escrow_dict(escrow))


@bp.post('/escrow/<int:eid>/release')
@jwt_required()
def release_escrow(eid):
    me = _current_user(); escrow = Escrow.query.get(eid)
    if not escrow:                  return _err('Not found.', 404)
    if escrow.employer_id != me.id: return _err('Forbidden.', 403)
    if escrow.status != 'held':     return _err('Escrow is not in held state.')
    escrow.status = 'released'
    sw = Wallet.query.filter_by(user_id=escrow.student_id).first()
    if not sw: sw = Wallet(user_id=escrow.student_id, balance=0.0); db.session.add(sw)
    sw.balance += escrow.amount; sw.updated_at = datetime.utcnow()
    db.session.add(Transaction(user_id=escrow.student_id, type='release', amount=escrow.amount, status='completed'))
    db.session.commit()
    return _ok(_escrow_dict(escrow))


@bp.post('/escrow/<int:eid>/cancel')
@jwt_required()
def cancel_escrow(eid):
    me = _current_user(); escrow = Escrow.query.get(eid)
    if not escrow:                  return _err('Not found.', 404)
    if escrow.employer_id != me.id: return _err('Forbidden.', 403)
    if escrow.status != 'held':     return _err('Cannot cancel: not held.')
    escrow.status = 'cancelled'
    wallet = Wallet.query.filter_by(user_id=me.id).first()
    wallet.balance += escrow.amount; wallet.updated_at = datetime.utcnow()
    db.session.add(Transaction(user_id=me.id, type='refund', amount=escrow.amount, status='completed'))
    db.session.commit()
    return _ok(_escrow_dict(escrow))


@bp.get('/escrow/as-employer')
@jwt_required()
def get_escrows_employer():
    me = _current_user()
    return _ok([_escrow_dict(e) for e in Escrow.query.filter_by(employer_id=me.id).order_by(Escrow.created_at.desc()).all()])


@bp.get('/escrow/as-student')
@jwt_required()
def get_escrows_student():
    me = _current_user()
    return _ok([_escrow_dict(e) for e in Escrow.query.filter_by(student_id=me.id).order_by(Escrow.created_at.desc()).all()])


# ═════════════════════════════════════════════════════════════════════════════
#  WITHDRAWALS
# ═════════════════════════════════════════════════════════════════════════════

def _wd_dict(w: Withdrawal) -> dict:
    return {'id': w.id, 'user_id': w.user_id, 'amount': float(w.amount),
            'payout_method': w.payout_method, 'account_number': w.account_number,
            'status': w.status, 'admin_note': w.admin_note,
            'created_at': w.created_at.isoformat() if w.created_at else None}


@bp.post('/wallet/withdraw')
@jwt_required()
def request_withdrawal():
    me = _current_user(); d = get_json()
    amount  = float_field(d, 'amount')
    method  = str_field(d, 'payout_method', 'ccp')
    account = str_field(d, 'account_number')
    if amount < 500:  return _err('Minimum withdrawal is 500 DZD.')
    if not account:   return _err('Account number required.')
    wallet = Wallet.query.filter_by(user_id=me.id).first()
    if not wallet or float(wallet.balance) < amount: return _err('Insufficient balance.')
    wallet.balance -= amount; wallet.updated_at = datetime.utcnow()
    wd = Withdrawal(user_id=me.id, amount=amount, payout_method=method,
                    account_number=account, status='pending')
    db.session.add(wd)
    db.session.add(Transaction(user_id=me.id, type='withdraw', amount=amount, status='pending'))
    db.session.commit()
    return _created(_wd_dict(wd))


@bp.get('/wallet/withdrawals')
@jwt_required()
def get_withdrawals():
    me = _current_user()
    return _ok([_wd_dict(w) for w in Withdrawal.query.filter_by(user_id=me.id).order_by(Withdrawal.created_at.desc()).all()])


# ═════════════════════════════════════════════════════════════════════════════
#  ADMIN
# ═════════════════════════════════════════════════════════════════════════════

def _admin_only():
    me = _current_user()
    return me if (me and me.type == 'admin') else None


@bp.get('/admin/users')
@jwt_required()
def admin_get_users():
    if not _admin_only(): return _err('Admin only.', 403)
    users = User.query.filter(User.type != 'admin').order_by(User.created_at.desc()).all()
    return _ok([_user_dict(u) for u in users])


@bp.post('/admin/users/<int:uid>/ban')
@jwt_required()
def admin_ban(uid):
    if not _admin_only(): return _err('Admin only.', 403)
    user = User.query.get(uid)
    if not user: return _err('Not found.', 404)
    user.is_banned = True; user.ban_reason = str_field(get_json(), 'reason', 'Banned by admin.')
    db.session.commit()
    return _ok(_user_dict(user))


@bp.post('/admin/users/<int:uid>/unban')
@jwt_required()
def admin_unban(uid):
    if not _admin_only(): return _err('Admin only.', 403)
    user = User.query.get(uid)
    if not user: return _err('Not found.', 404)
    user.is_banned = False; user.ban_reason = None
    db.session.commit()
    return _ok(_user_dict(user))


@bp.post('/admin/users/<int:uid>/warn')
@jwt_required()
def admin_warn(uid):
    if not _admin_only(): return _err('Admin only.', 403)
    user = User.query.get(uid)
    if not user: return _err('Not found.', 404)
    user.warnings = (user.warnings or 0) + 1
    auto_banned = False
    if user.warnings >= 3:
        user.is_banned = True; user.ban_reason = 'Automatically banned after 3 warnings.'
        auto_banned = True
    db.session.commit()
    return _ok({**_user_dict(user), 'auto_banned': auto_banned})


@bp.get('/admin/withdrawals')
@jwt_required()
def admin_get_withdrawals():
    if not _admin_only(): return _err('Admin only.', 403)
    def wd_full(w):
        u = User.query.get(w.user_id); d = _wd_dict(w)
        d['user'] = {'id': u.id, 'firstname': u.firstname, 'lastname': u.lastname,
                     'email': u.email, 'image': u.image} if u else None
        return d
    return _ok([wd_full(w) for w in Withdrawal.query.order_by(Withdrawal.created_at.asc()).all()])


@bp.post('/admin/withdrawals/<int:wid>/approve')
@jwt_required()
def admin_approve_withdrawal(wid):
    if not _admin_only(): return _err('Admin only.', 403)
    wd = Withdrawal.query.get(wid)
    if not wd:               return _err('Not found.', 404)
    if wd.status != 'pending': return _err('Already processed.')
    wd.status = 'approved'; wd.admin_note = str_field(get_json(), 'note') or None
    tx = Transaction.query.filter_by(user_id=wd.user_id, type='withdraw', status='pending').first()
    if tx: tx.status = 'completed'
    db.session.commit()
    return _ok(_wd_dict(wd))


@bp.post('/admin/withdrawals/<int:wid>/reject')
@jwt_required()
def admin_reject_withdrawal(wid):
    if not _admin_only(): return _err('Admin only.', 403)
    wd = Withdrawal.query.get(wid)
    if not wd:               return _err('Not found.', 404)
    if wd.status != 'pending': return _err('Already processed.')
    wd.status = 'rejected'; wd.admin_note = str_field(get_json(), 'note') or None
    wallet = Wallet.query.filter_by(user_id=wd.user_id).first()
    if wallet: wallet.balance += wd.amount; wallet.updated_at = datetime.utcnow()
    tx = Transaction.query.filter_by(user_id=wd.user_id, type='withdraw', status='pending').first()
    if tx: tx.status = 'failed'
    db.session.add(Transaction(user_id=wd.user_id, type='refund', amount=wd.amount, status='completed'))
    db.session.commit()
    return _ok(_wd_dict(wd))


@bp.post('/admin/events')
@jwt_required()
def admin_create_event():
    me = _admin_only()
    if not me: return _err('Admin only.', 403)
    d = get_json()
    e = Event(title=str_field(d,'title'), description=str_field(d,'description'),
              image=d.get('image'), location=d.get('location'),
              start_at=datetime.fromisoformat(d['start_at']) if d.get('start_at') else None,
              end_at  =datetime.fromisoformat(d['end_at'])   if d.get('end_at')   else None,
              event_type=str_field(d,'event_type','other'), capacity=d.get('capacity'), is_visible=True)
    db.session.add(e); db.session.commit()
    try:
        for u in User.query.filter(User.type != 'admin', User.is_banned == False).all():
            if u.email: _send_event_email(u, e)
    except Exception: pass
    return _created(_event_dict(e))


def _send_event_email(user: User, event: Event):
    html = f"""<html><body style="font-family:Cairo,sans-serif;background:#F5F3FF;padding:32px;">
<div style="max-width:520px;margin:0 auto;background:#fff;border-radius:18px;overflow:hidden;
            box-shadow:0 8px 32px rgba(26,10,46,0.1);">
  <div style="background:linear-gradient(135deg,#3B0F8C,#7C3AED);padding:40px;text-align:center;">
    <span style="background:rgba(217,119,6,0.2);border:1px solid #D97706;border-radius:100px;
                 padding:4px 18px;font-size:10px;letter-spacing:0.18em;text-transform:uppercase;
                 color:#D97706;display:inline-block;margin-bottom:14px;">New Event</span>
    <h1 style="color:#fff;margin:0;font-size:24px;">{event.title}</h1>
  </div>
  <div style="padding:36px;">
    <p style="font-size:15px;color:#444;line-height:1.8;">Dear {user.firstname},<br/><br/>{event.description or ''}</p>
    <table style="background:#F5F3FF;border-radius:12px;padding:18px;width:100%;border-collapse:collapse;">
      <tr><td style="padding:8px;color:#5B21B6;font-weight:700;">📅 Start</td>
          <td style="padding:8px;">{event.start_at.strftime("%A, %B %d %Y at %H:%M") if event.start_at else "—"}</td></tr>
      <tr><td style="padding:8px;color:#5B21B6;font-weight:700;">📍 Location</td>
          <td style="padding:8px;">{event.location or "—"}</td></tr>
    </table>
  </div>
</div></body></html>"""
    _send_email(user.email, f'New Event: {event.title} — {PLATFORM_NAME}', html)


@bp.post('/admin/announcements')
@jwt_required()
def admin_create_announcement():
    me = _admin_only()
    if not me: return _err('Admin only.', 403)
    d = get_json()
    a = Announcement(title=str_field(d,'title'), content=str_field(d,'content'),
                     image=d.get('image'), is_pinned=bool_field(d,'is_pinned'),
                     is_visible=True, author_id=me.id)
    db.session.add(a); db.session.commit()
    return _created(_ann_dict(a))

@bp.route('/')
def api_root():
    return {"ok": True, "message": "Talib-Awn API is running 🚀"}