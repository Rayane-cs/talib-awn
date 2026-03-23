# ══════════════════════════════════════════════════════════════════════════════
#  routes_talib.py  —  Talib-Awn · طالب عون
#  Flask Blueprint: all API routes for the Talib-Awn student jobs platform.
#
#  Pattern borrowed from friend's routes.py (OTP, email, JWT structure)
#  and extended for jobs, wallet, escrow, withdrawals, admin.
#
#  Mount in your app.py:
#    from routes_talib import talib_bp
#    app.register_blueprint(talib_bp, url_prefix='/api')
# ══════════════════════════════════════════════════════════════════════════════

import random, string, time, os
from datetime import datetime, timedelta

from flask import Blueprint, request, jsonify, g
from flask_cors import cross_origin
from flask_jwt_extended import (
    jwt_required, create_access_token, create_refresh_token,
    get_jwt_identity, verify_jwt_in_request,
)
from werkzeug.security import check_password_hash, generate_password_hash

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ─── import your models (adjust path to match your project) ──────────────────
from models_talib import (
    db, User, Project, ProjectLike, ProjectComment,
    Event, EventRegistration, Announcement, UserFollow,
    Wallet, Transaction, Escrow, Withdrawal,
)

talib_bp = Blueprint('talib', __name__)

# ─────────────────────────────────────────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────────────────────────────────────────
GMAIL_ADDRESS  = os.environ.get('GMAIL_ADDRESS',  'universitychlefclub@gmail.com')
GMAIL_APP_PASS = os.environ.get('GMAIL_APP_PASS',  'rqki cvlk iqgr smdj')
PLATFORM_NAME  = 'طالب-عون (Talib-Awn)'
OTP_EXPIRY_SEC = 120

HTTP_200 = 200; HTTP_201 = 201; HTTP_400 = 400
HTTP_401 = 401; HTTP_403 = 403; HTTP_404 = 404; HTTP_409 = 409

# In-memory OTP stores  {email: {otp, sent_at, data}}
_pending_registrations: dict = {}
_pending_resets:         dict = {}

VALID_GRADES  = ['Student', 'Professor', 'Researcher', 'Company manager']
VALID_DOMAINS = [
    'intelligence artificielle', 'developpement web', 'cyber securite',
    'reseaux et telecommunications', 'systemes embarques',
    'science des donnees', 'genie logiciel', 'autre',
]


# ═════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ═════════════════════════════════════════════════════════════════════════════

def _otp() -> str:
    return ''.join(random.choices(string.digits, k=8))

def _ok(data=None, **kwargs):
    r = {'ok': True}
    if data is not None: r['data'] = data
    r.update(kwargs)
    return jsonify(r), HTTP_200

def _created(data=None, **kwargs):
    r = {'ok': True}
    if data is not None: r['data'] = data
    r.update(kwargs)
    return jsonify(r), HTTP_201

def _err(msg, code=HTTP_400):
    return jsonify({'ok': False, 'error': msg}), code

def _current_user():
    """Return User row for the JWT caller, or None."""
    try:
        verify_jwt_in_request()
        uid = get_jwt_identity()
        return User.query.get(uid)
    except Exception:
        return None

def _user_dict(u: User) -> dict:
    return {
        'id': u.id, 'firstname': u.firstname, 'lastname': u.lastname,
        'email': u.email, 'phone': u.phone, 'image': u.image,
        'role': u.role, 'grade': u.grade, 'domain': u.domain,
        'institution': getattr(u, 'institution', None),
        'field_of_study': getattr(u, 'field_of_study', None),
        'student_id_number': getattr(u, 'student_id_number', None),
        'company_name': getattr(u, 'company_name', None),
        'is_banned': u.is_banned, 'ban_reason': u.ban_reason,
        'warnings': getattr(u, 'warnings', 0),
        'is_verified': getattr(u, 'is_verified', False),
        'created_at': u.created_at.isoformat() if u.created_at else None,
    }

def _send_email(to: str, subject: str, html: str):
    """Generic HTML email sender via Gmail SMTP."""
    msg = MIMEMultipart('alternative')
    msg['From']    = f'{PLATFORM_NAME} <{GMAIL_ADDRESS}>'
    msg['To']      = to
    msg['Subject'] = subject
    msg.attach(MIMEText(html, 'html'))
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
        s.login(GMAIL_ADDRESS, GMAIL_APP_PASS)
        s.sendmail(GMAIL_ADDRESS, to, msg.as_string())

def _otp_email_html(otp: str) -> str:
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
           style="background:#fff;border-radius:20px;overflow:hidden;
                  box-shadow:0 8px 40px rgba(26,10,46,0.1);">
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
          <p style="margin:0 0 16px;font-size:11px;letter-spacing:0.15em;text-transform:uppercase;color:#999;text-align:center;">
            Your OTP Code
          </p>
          <table cellpadding="0" cellspacing="0" border="0" style="margin:0 auto;"><tr>{cells}</tr></table>
        </div>
        <div style="background:#FEF3C7;border:1px solid #D97706;border-radius:10px;padding:12px 20px;margin-bottom:28px;">
          <p style="margin:0;font-family:sans-serif;font-size:12px;color:#92400E;">
            ⏰ Expires in {OTP_EXPIRY_SEC // 60} minutes. Do not share it with anyone.
          </p>
        </div>
        <p style="font-family:sans-serif;font-size:12px;color:#ccc;margin:0;">
          If you didn't request this, ignore this email.
        </p>
      </td></tr>
      <tr><td style="background:#F5F3FF;padding:24px;text-align:center;border-top:1px solid #EDE9FE;">
        <p style="font-family:sans-serif;font-size:11px;color:#bbb;margin:0;">
          © 2026 {PLATFORM_NAME} · Algeria
        </p>
      </td></tr>
    </table></td></tr></table></body></html>"""


# ═════════════════════════════════════════════════════════════════════════════
#  AUTH — REGISTER
# ═════════════════════════════════════════════════════════════════════════════

@talib_bp.post('/auth/register/send-otp')
def register_send_otp():
    """
    Step 1: validate fields, generate OTP, send email.
    Body: { email, password, firstname, lastname, grade, domain?,
            phone?, institution?, field_of_study?, student_id_number?,
            company_name? }
    """
    d = request.get_json(silent=True) or {}
    email     = (d.get('email') or '').strip().lower()
    password  = d.get('password') or ''
    firstname = (d.get('firstname') or '').strip()
    lastname  = (d.get('lastname') or '').strip()
    grade     = (d.get('grade') or '').strip()
    domain    = (d.get('domain') or 'autre').strip().lower()
    phone     = (d.get('phone') or '').strip()

    if not email or '@' not in email:
        return _err('Valid email required.')
    if len(password) < 6:
        return _err('Password must be at least 6 characters.')
    if not firstname:
        return _err('First name required.')
    if grade not in VALID_GRADES:
        return _err(f'Grade must be one of: {", ".join(VALID_GRADES)}')
    if domain not in VALID_DOMAINS:
        domain = 'autre'

    # Check duplicate
    if User.query.filter_by(email=email).first():
        return _err('An account with this email already exists.', HTTP_409)

    otp = _otp()
    _pending_registrations[email] = {
        'otp':      otp,
        'sent_at':  time.time(),
        'data': {
            'email':             email,
            'password_hash':     generate_password_hash(password),
            'firstname':         firstname,
            'lastname':          lastname,
            'grade':             grade,
            'domain':            domain,
            'phone':             phone,
            'institution':       d.get('institution', ''),
            'field_of_study':    d.get('field_of_study', ''),
            'student_id_number': d.get('student_id_number', ''),
            'company_name':      d.get('company_name', ''),
        }
    }

    try:
        _send_email(email, f'Your Verification Code — {PLATFORM_NAME}', _otp_email_html(otp))
    except Exception as e:
        return _err(f'Failed to send email: {str(e)}')

    return _ok(message='OTP sent to email.')


@talib_bp.post('/auth/register/verify-otp')
def register_verify_otp():
    """
    Step 2: verify OTP, create user, return JWT.
    Body: { email, otp }
    """
    d     = request.get_json(silent=True) or {}
    email = (d.get('email') or '').strip().lower()
    otp   = (d.get('otp')   or '').strip()

    pending = _pending_registrations.get(email)
    if not pending:
        return _err('No pending registration for this email. Please restart.')

    if time.time() - pending['sent_at'] > OTP_EXPIRY_SEC:
        _pending_registrations.pop(email, None)
        return _err('OTP expired. Please request a new one.')

    if pending['otp'] != otp:
        return _err('Incorrect OTP.')

    reg = pending['data']
    _pending_registrations.pop(email, None)

    # Double-check duplicate (race condition)
    if User.query.filter_by(email=email).first():
        return _err('Account already exists.', HTTP_409)

    user = User(
        email             = reg['email'],
        password_hash     = reg['password_hash'],
        firstname         = reg['firstname'],
        lastname          = reg['lastname'],
        grade             = reg['grade'],
        domain            = reg['domain'],
        phone             = reg['phone'],
        institution       = reg['institution'],
        field_of_study    = reg['field_of_study'],
        student_id_number = reg['student_id_number'],
        company_name      = reg['company_name'],
        role              = 'client',
        is_verified       = True,
        is_banned         = False,
        warnings          = 0,
    )
    db.session.add(user)
    db.session.flush()   # get user.id

    # Create wallet
    wallet = Wallet(user_id=user.id, balance=0.0)
    db.session.add(wallet)
    db.session.commit()

    access  = create_access_token(identity=user.id,
                                  expires_delta=timedelta(days=7))
    refresh = create_refresh_token(identity=user.id,
                                   expires_delta=timedelta(days=30))

    return _created({'user': _user_dict(user),
                     'access_token': access,
                     'refresh_token': refresh})


# ═════════════════════════════════════════════════════════════════════════════
#  AUTH — LOGIN / LOGOUT / REFRESH
# ═════════════════════════════════════════════════════════════════════════════

@talib_bp.post('/auth/login')
def login():
    """Body: { email, password }"""
    d        = request.get_json(silent=True) or {}
    email    = (d.get('email') or '').strip().lower()
    password = d.get('password') or ''

    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        return _err('Invalid email or password.', HTTP_401)

    if user.is_banned:
        return _err(f'Account suspended. Reason: {user.ban_reason}', HTTP_403)

    access  = create_access_token(identity=user.id,
                                  expires_delta=timedelta(days=7))
    refresh = create_refresh_token(identity=user.id,
                                   expires_delta=timedelta(days=30))

    return _ok({'user': _user_dict(user),
                'access_token': access,
                'refresh_token': refresh})


@talib_bp.post('/auth/refresh')
@jwt_required(refresh=True)
def refresh_token():
    uid = get_jwt_identity()
    access = create_access_token(identity=uid, expires_delta=timedelta(days=7))
    return _ok({'access_token': access})


@talib_bp.get('/auth/me')
@jwt_required()
def get_me():
    user = _current_user()
    if not user: return _err('User not found.', HTTP_404)
    return _ok(_user_dict(user))


# ═════════════════════════════════════════════════════════════════════════════
#  AUTH — PASSWORD RESET
# ═════════════════════════════════════════════════════════════════════════════

@talib_bp.post('/auth/reset/send-otp')
def reset_send_otp():
    """Body: { email }"""
    email = ((request.get_json(silent=True) or {}).get('email') or '').strip().lower()
    user  = User.query.filter_by(email=email).first()
    if not user:
        # Don't reveal existence — still return OK
        return _ok(message='If that email exists, an OTP was sent.')

    otp = _otp()
    _pending_resets[email] = {'otp': otp, 'sent_at': time.time()}
    try:
        _send_email(email, f'Password Reset — {PLATFORM_NAME}', _otp_email_html(otp))
    except Exception as e:
        return _err(f'Failed to send email: {str(e)}')
    return _ok(message='OTP sent.')


@talib_bp.post('/auth/reset/verify-otp')
def reset_verify_otp():
    """Body: { email, otp }"""
    d     = request.get_json(silent=True) or {}
    email = (d.get('email') or '').strip().lower()
    otp   = (d.get('otp')   or '').strip()

    p = _pending_resets.get(email)
    if not p:                                 return _err('No reset pending.')
    if time.time() - p['sent_at'] > OTP_EXPIRY_SEC:
        _pending_resets.pop(email, None);    return _err('OTP expired.')
    if p['otp'] != otp:                       return _err('Incorrect OTP.')

    # Mark as verified but leave entry so /reset/set-password can use it
    _pending_resets[email]['verified'] = True
    return _ok(message='OTP verified.')


@talib_bp.post('/auth/reset/set-password')
def reset_set_password():
    """Body: { email, otp, new_password }"""
    d            = request.get_json(silent=True) or {}
    email        = (d.get('email') or '').strip().lower()
    otp          = (d.get('otp')   or '').strip()
    new_password = d.get('new_password') or ''

    p = _pending_resets.get(email)
    if not p or not p.get('verified'):        return _err('OTP not verified.')
    if p['otp'] != otp:                       return _err('OTP mismatch.')
    if len(new_password) < 6:                 return _err('Password too short.')

    user = User.query.filter_by(email=email).first()
    if not user: return _err('User not found.', HTTP_404)

    user.password_hash = generate_password_hash(new_password)
    db.session.commit()
    _pending_resets.pop(email, None)
    return _ok(message='Password updated.')


# ═════════════════════════════════════════════════════════════════════════════
#  PROFILE
# ═════════════════════════════════════════════════════════════════════════════

@talib_bp.patch('/users/me')
@jwt_required()
def update_profile():
    """Update own profile. Body: any subset of editable fields."""
    user = _current_user()
    if not user: return _err('Not found.', HTTP_404)
    d = request.get_json(silent=True) or {}

    EDITABLE = ['firstname', 'lastname', 'phone', 'image',
                'domain', 'institution', 'field_of_study',
                'student_id_number', 'company_name']
    for field in EDITABLE:
        if field in d:
            setattr(user, field, d[field])

    db.session.commit()
    return _ok(_user_dict(user))


@talib_bp.patch('/users/me/password')
@jwt_required()
def change_password():
    """Body: { current_password, new_password }"""
    user = _current_user()
    if not user: return _err('Not found.', HTTP_404)
    d = request.get_json(silent=True) or {}

    if not check_password_hash(user.password_hash, d.get('current_password', '')):
        return _err('Current password incorrect.', HTTP_401)
    new_pw = d.get('new_password', '')
    if len(new_pw) < 6: return _err('Password too short.')
    user.password_hash = generate_password_hash(new_pw)
    db.session.commit()
    return _ok(message='Password changed.')


@talib_bp.get('/users/<int:uid>')
@jwt_required()
def get_user_info(uid):
    """Public profile + projects + follow counts."""
    me   = _current_user()
    user = User.query.get(uid)
    if not user: return _err('User not found.', HTTP_404)

    projects = (Project.query
                .filter_by(owner_id=uid, is_visible=True)
                .order_by(Project.created_at.desc()).all())

    followers_count = UserFollow.query.filter_by(following_id=uid).count()
    following_count = UserFollow.query.filter_by(follower_id=uid).count()
    is_following    = bool(me and UserFollow.query.filter_by(
        follower_id=me.id, following_id=uid).first())

    info = _user_dict(user)
    info.update({'followers_count': followers_count,
                 'following_count': following_count,
                 'is_following':    is_following})

    return _ok({
        'user':     info,
        'projects': [_proj_dict(p) for p in projects],
    })


@talib_bp.get('/users/search')
@jwt_required()
def search_users():
    """?q=name"""
    q    = (request.args.get('q') or '').strip()
    users = (User.query
             .filter(
                 (User.firstname.ilike(f'%{q}%')) |
                 (User.lastname.ilike(f'%{q}%'))
             ).limit(20).all())
    return _ok([_user_dict(u) for u in users])


# ═════════════════════════════════════════════════════════════════════════════
#  SOCIAL — FOLLOW / UNFOLLOW
# ═════════════════════════════════════════════════════════════════════════════

@talib_bp.post('/users/<int:uid>/follow')
@jwt_required()
def toggle_follow(uid):
    me = _current_user()
    if not me: return _err('Not authenticated.', HTTP_401)
    if me.id == uid: return _err('Cannot follow yourself.')

    existing = UserFollow.query.filter_by(follower_id=me.id, following_id=uid).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        return _ok({'following': False})

    db.session.add(UserFollow(follower_id=me.id, following_id=uid))
    db.session.commit()

    # Send follow email (best-effort, non-blocking)
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
        <p style="font-size:15px;color:#444;">
          <strong style="color:#5B21B6;">{name}</strong> started following you on {PLATFORM_NAME}.
        </p>
      </div>
    </div></body></html>"""
    _send_email(target.email, f'{name} started following you — {PLATFORM_NAME}', html)


# ═════════════════════════════════════════════════════════════════════════════
#  PROJECTS
# ═════════════════════════════════════════════════════════════════════════════

def _proj_dict(p: Project, me_id=None) -> dict:
    liked = False
    if me_id:
        liked = bool(ProjectLike.query.filter_by(project_id=p.id, user_id=me_id).first())
    owner = User.query.get(p.owner_id)
    return {
        'id':            p.id,
        'title':         p.title,
        'description':   p.description,
        'image':         p.image,
        'category':      p.category,
        'status':        p.status,
        'owner_id':      p.owner_id,
        'created_at':    p.created_at.isoformat() if p.created_at else None,
        'like_count':    ProjectLike.query.filter_by(project_id=p.id).count(),
        'comment_count': ProjectComment.query.filter_by(project_id=p.id).count(),
        'is_liked':      liked,
        'owner': {
            'id': owner.id, 'firstname': owner.firstname,
            'lastname': owner.lastname, 'image': owner.image,
            'grade': owner.grade, 'domain': owner.domain,
        } if owner else None,
    }


@talib_bp.get('/projects')
@jwt_required(optional=True)
def get_projects():
    """?category=web  — optional filter"""
    me       = _current_user()
    category = request.args.get('category')
    q = Project.query.filter_by(is_visible=True).order_by(Project.created_at.desc())
    if category and category != 'all':
        q = q.filter_by(category=category)
    return _ok([_proj_dict(p, me.id if me else None) for p in q.all()])


@talib_bp.post('/projects')
@jwt_required()
def create_project():
    me = _current_user()
    if not me: return _err('Not authenticated.', HTTP_401)
    d = request.get_json(silent=True) or {}
    p = Project(
        title       = d.get('title', ''),
        description = d.get('description', ''),
        image       = d.get('image'),
        category    = d.get('category', 'autre'),
        status      = d.get('status', 'open'),
        owner_id    = me.id,
        is_visible  = True,
    )
    db.session.add(p); db.session.commit()
    return _created(_proj_dict(p, me.id))


@talib_bp.patch('/projects/<int:pid>')
@jwt_required()
def update_project(pid):
    me = _current_user()
    p  = Project.query.get(pid)
    if not p: return _err('Not found.', HTTP_404)
    if p.owner_id != me.id and me.role != 'Admin':
        return _err('Forbidden.', HTTP_403)
    d = request.get_json(silent=True) or {}
    for f in ['title', 'description', 'image', 'category', 'status']:
        if f in d: setattr(p, f, d[f])
    db.session.commit()
    return _ok(_proj_dict(p, me.id))


@talib_bp.delete('/projects/<int:pid>')
@jwt_required()
def delete_project(pid):
    me = _current_user()
    p  = Project.query.get(pid)
    if not p: return _err('Not found.', HTTP_404)
    if p.owner_id != me.id and me.role != 'Admin':
        return _err('Forbidden.', HTTP_403)
    db.session.delete(p); db.session.commit()
    return _ok(message='Deleted.')


@talib_bp.post('/projects/<int:pid>/like')
@jwt_required()
def toggle_like(pid):
    me = _current_user()
    if not me: return _err('Not authenticated.', HTTP_401)
    existing = ProjectLike.query.filter_by(project_id=pid, user_id=me.id).first()
    if existing:
        db.session.delete(existing); db.session.commit()
        return _ok({'liked': False})
    db.session.add(ProjectLike(project_id=pid, user_id=me.id))
    db.session.commit()
    return _ok({'liked': True})


@talib_bp.get('/projects/<int:pid>/comments')
@jwt_required(optional=True)
def get_comments(pid):
    comments = (ProjectComment.query.filter_by(project_id=pid)
                .order_by(ProjectComment.created_at.asc()).all())
    def c_dict(c):
        user = User.query.get(c.user_id)
        return {
            'id': c.id, 'content': c.content,
            'created_at': c.created_at.isoformat() if c.created_at else None,
            'user_id': c.user_id,
            'user': {'id': user.id, 'firstname': user.firstname,
                     'lastname': user.lastname, 'image': user.image} if user else None,
        }
    return _ok([c_dict(c) for c in comments])


@talib_bp.post('/projects/<int:pid>/comments')
@jwt_required()
def add_comment(pid):
    me = _current_user()
    if not me: return _err('Not authenticated.', HTTP_401)
    d  = request.get_json(silent=True) or {}
    c  = ProjectComment(project_id=pid, user_id=me.id, content=d.get('content', ''))
    db.session.add(c); db.session.commit()
    user = me
    return _created({
        'id': c.id, 'content': c.content,
        'created_at': c.created_at.isoformat() if c.created_at else None,
        'user_id': c.user_id,
        'user': {'id': user.id, 'firstname': user.firstname,
                 'lastname': user.lastname, 'image': user.image},
    })


@talib_bp.delete('/comments/<int:cid>')
@jwt_required()
def delete_comment(cid):
    me = _current_user()
    c  = ProjectComment.query.get(cid)
    if not c: return _err('Not found.', HTTP_404)
    if c.user_id != me.id and me.role != 'Admin':
        return _err('Forbidden.', HTTP_403)
    db.session.delete(c); db.session.commit()
    return _ok(message='Deleted.')


# ═════════════════════════════════════════════════════════════════════════════
#  EVENTS
# ═════════════════════════════════════════════════════════════════════════════

def _event_dict(e: Event, me_id=None) -> dict:
    reg_count = EventRegistration.query.filter_by(event_id=e.id).count()
    is_registered = False
    if me_id:
        is_registered = bool(EventRegistration.query.filter_by(
            event_id=e.id, user_id=me_id).first())
    return {
        'id': e.id, 'title': e.title, 'description': e.description,
        'image': e.image, 'location': e.location,
        'start_at': e.start_at.isoformat() if e.start_at else None,
        'end_at':   e.end_at.isoformat()   if e.end_at   else None,
        'event_type': getattr(e, 'event_type', None),
        'capacity':   getattr(e, 'capacity', None),
        'is_visible': e.is_visible,
        'created_at': e.created_at.isoformat() if e.created_at else None,
        'registration_count': reg_count,
        'is_registered': is_registered,
    }


@talib_bp.get('/events')
@jwt_required(optional=True)
def get_events():
    me = _current_user()
    events = (Event.query.filter_by(is_visible=True)
              .order_by(Event.start_at.asc()).all())
    return _ok([_event_dict(e, me.id if me else None) for e in events])


@talib_bp.post('/events/<int:eid>/register')
@jwt_required()
def join_event(eid):
    me = _current_user()
    if not me: return _err('Not authenticated.', HTTP_401)
    if EventRegistration.query.filter_by(event_id=eid, user_id=me.id).first():
        return _err('Already registered.', HTTP_409)
    db.session.add(EventRegistration(event_id=eid, user_id=me.id))
    db.session.commit()
    return _ok(message='Registered.')


@talib_bp.delete('/events/<int:eid>/register')
@jwt_required()
def quit_event(eid):
    me  = _current_user()
    reg = EventRegistration.query.filter_by(event_id=eid, user_id=me.id).first()
    if not reg: return _err('Not registered.', HTTP_404)
    db.session.delete(reg); db.session.commit()
    return _ok(message='Unregistered.')


# ═════════════════════════════════════════════════════════════════════════════
#  ANNOUNCEMENTS
# ═════════════════════════════════════════════════════════════════════════════

def _ann_dict(a: Announcement) -> dict:
    author = User.query.get(a.author_id) if a.author_id else None
    return {
        'id': a.id, 'title': getattr(a, 'title', ''),
        'content': a.content, 'image': getattr(a, 'image', None),
        'is_pinned': getattr(a, 'is_pinned', False),
        'is_visible': a.is_visible,
        'created_at': a.created_at.isoformat() if a.created_at else None,
        'author': {
            'firstname': author.firstname, 'lastname': author.lastname,
            'image': author.image,
        } if author else None,
    }


@talib_bp.get('/announcements')
@jwt_required(optional=True)
def get_announcements():
    anns = (Announcement.query.filter_by(is_visible=True)
            .order_by(Announcement.is_pinned.desc(),
                      Announcement.created_at.desc()).all())
    return _ok([_ann_dict(a) for a in anns])


# ═════════════════════════════════════════════════════════════════════════════
#  STATS
# ═════════════════════════════════════════════════════════════════════════════

@talib_bp.get('/stats')
def get_stats():
    return _ok({
        'projects': Project.query.filter_by(is_visible=True).count(),
        'events':   Event.query.filter_by(is_visible=True).count(),
        'users':    User.query.filter(User.role != 'Admin').count(),
    })


# ═════════════════════════════════════════════════════════════════════════════
#  WALLET — BALANCE & TRANSACTIONS
# ═════════════════════════════════════════════════════════════════════════════

def _wallet_dict(w: Wallet) -> dict:
    return {
        'user_id':    w.user_id,
        'balance':    float(w.balance),
        'updated_at': w.updated_at.isoformat() if w.updated_at else None,
    }


def _tx_dict(t: Transaction) -> dict:
    return {
        'id':         t.id,
        'user_id':    t.user_id,
        'type':       t.type,
        'amount':     float(t.amount),
        'status':     t.status,
        'reference':  t.reference,
        'created_at': t.created_at.isoformat() if t.created_at else None,
    }


@talib_bp.get('/wallet')
@jwt_required()
def get_wallet():
    me = _current_user()
    w  = Wallet.query.filter_by(user_id=me.id).first()
    if not w:
        w = Wallet(user_id=me.id, balance=0.0)
        db.session.add(w); db.session.commit()
    return _ok(_wallet_dict(w))


@talib_bp.get('/wallet/transactions')
@jwt_required()
def get_transactions():
    me    = _current_user()
    limit = min(int(request.args.get('limit', 50)), 200)
    txs   = (Transaction.query.filter_by(user_id=me.id)
             .order_by(Transaction.created_at.desc()).limit(limit).all())
    return _ok([_tx_dict(t) for t in txs])


# ═════════════════════════════════════════════════════════════════════════════
#  WALLET — DEPOSIT  (manual admin-confirmed, or Chargily webhook)
# ═════════════════════════════════════════════════════════════════════════════

@talib_bp.post('/wallet/deposit')
@jwt_required()
def request_deposit():
    """
    For manual/CCP deposits.
    Body: { amount }
    Creates a PENDING transaction. Admin confirms via /admin/transactions/<id>/complete
    """
    me = _current_user()
    d  = request.get_json(silent=True) or {}
    try:
        amount = float(d.get('amount', 0))
    except (TypeError, ValueError):
        return _err('Invalid amount.')
    if amount < 100:   return _err('Minimum deposit is 100 DZD.')
    if amount > 200000: return _err('Maximum deposit is 200,000 DZD.')

    tx = Transaction(
        user_id   = me.id,
        type      = 'deposit',
        amount    = amount,
        status    = 'pending',
        reference = 'manual-' + _otp(),
    )
    db.session.add(tx); db.session.commit()
    return _created(_tx_dict(tx))


# Chargily webhook — called by Chargily server after payment
@talib_bp.post('/webhook/chargily')
def chargily_webhook():
    """
    Chargily sends POST with payment result.
    In production, verify Chargily signature.
    """
    payload = request.get_json(silent=True) or {}
    # Minimal: status, metadata.user_id, amount
    if payload.get('status') != 'paid':
        return jsonify({'ok': True}), HTTP_200

    meta    = payload.get('metadata', {})
    user_id = meta.get('user_id')
    amount  = float(payload.get('amount', 0))
    ref     = payload.get('id', '')

    if not user_id or amount <= 0:
        return jsonify({'ok': False, 'error': 'bad payload'}), HTTP_400

    # Idempotency: skip if reference already processed
    if Transaction.query.filter_by(reference=ref, status='completed').first():
        return jsonify({'ok': True}), HTTP_200

    wallet = Wallet.query.filter_by(user_id=user_id).first()
    if not wallet:
        wallet = Wallet(user_id=user_id, balance=0.0)
        db.session.add(wallet)

    wallet.balance += amount
    wallet.updated_at = datetime.utcnow()

    tx = Transaction(user_id=user_id, type='deposit',
                     amount=amount, status='completed', reference=ref)
    db.session.add(tx)
    db.session.commit()
    return jsonify({'ok': True}), HTTP_200


# ═════════════════════════════════════════════════════════════════════════════
#  WALLET — ESCROW
# ═════════════════════════════════════════════════════════════════════════════

def _escrow_dict(e: Escrow) -> dict:
    student  = User.query.get(e.student_id)
    employer = User.query.get(e.employer_id)
    return {
        'id':          e.id,
        'employer_id': e.employer_id,
        'student_id':  e.student_id,
        'amount':      float(e.amount),
        'status':      e.status,
        'note':        e.note,
        'job_id':      e.job_id,
        'created_at':  e.created_at.isoformat() if e.created_at else None,
        'student':  {'id': student.id,  'firstname': student.firstname,
                     'lastname': student.lastname, 'image': student.image}
                    if student else None,
        'employer': {'id': employer.id, 'firstname': employer.firstname,
                     'lastname': employer.lastname, 'image': employer.image}
                    if employer else None,
    }


@talib_bp.post('/escrow')
@jwt_required()
def create_escrow():
    """Employer locks funds for a student. Body: { student_id, amount, job_id?, note? }"""
    me = _current_user()
    d  = request.get_json(silent=True) or {}
    try:
        amount = float(d['amount'])
    except (KeyError, TypeError, ValueError):
        return _err('amount required.')
    student_id = d.get('student_id')
    if not student_id: return _err('student_id required.')

    wallet = Wallet.query.filter_by(user_id=me.id).first()
    if not wallet or wallet.balance < amount:
        return _err('Insufficient balance.')

    wallet.balance -= amount
    wallet.updated_at = datetime.utcnow()

    escrow = Escrow(employer_id=me.id, student_id=student_id,
                    amount=amount, status='held',
                    job_id=d.get('job_id'), note=d.get('note'))
    db.session.add(escrow)

    tx = Transaction(user_id=me.id, type='escrow',
                     amount=amount, status='completed')
    db.session.add(tx)
    db.session.commit()
    return _created(_escrow_dict(escrow))


@talib_bp.post('/escrow/<int:eid>/release')
@jwt_required()
def release_escrow(eid):
    """Employer releases escrow to student (job done)."""
    me     = _current_user()
    escrow = Escrow.query.get(eid)
    if not escrow:                        return _err('Not found.', HTTP_404)
    if escrow.employer_id != me.id:       return _err('Forbidden.', HTTP_403)
    if escrow.status != 'held':           return _err('Escrow not in held state.')

    escrow.status = 'released'
    student_wallet = Wallet.query.filter_by(user_id=escrow.student_id).first()
    if not student_wallet:
        student_wallet = Wallet(user_id=escrow.student_id, balance=0.0)
        db.session.add(student_wallet)

    student_wallet.balance   += escrow.amount
    student_wallet.updated_at = datetime.utcnow()

    db.session.add(Transaction(user_id=escrow.student_id, type='release',
                               amount=escrow.amount, status='completed'))
    db.session.commit()
    return _ok(_escrow_dict(escrow))


@talib_bp.post('/escrow/<int:eid>/cancel')
@jwt_required()
def cancel_escrow(eid):
    """Employer cancels escrow — refund to employer wallet."""
    me     = _current_user()
    escrow = Escrow.query.get(eid)
    if not escrow:                  return _err('Not found.', HTTP_404)
    if escrow.employer_id != me.id: return _err('Forbidden.', HTTP_403)
    if escrow.status != 'held':     return _err('Cannot cancel: not held.')

    escrow.status = 'cancelled'
    wallet = Wallet.query.filter_by(user_id=me.id).first()
    wallet.balance   += escrow.amount
    wallet.updated_at = datetime.utcnow()

    db.session.add(Transaction(user_id=me.id, type='refund',
                               amount=escrow.amount, status='completed'))
    db.session.commit()
    return _ok(_escrow_dict(escrow))


@talib_bp.get('/escrow/as-employer')
@jwt_required()
def get_escrows_employer():
    me = _current_user()
    es = Escrow.query.filter_by(employer_id=me.id).order_by(
        Escrow.created_at.desc()).all()
    return _ok([_escrow_dict(e) for e in es])


@talib_bp.get('/escrow/as-student')
@jwt_required()
def get_escrows_student():
    me = _current_user()
    es = Escrow.query.filter_by(student_id=me.id).order_by(
        Escrow.created_at.desc()).all()
    return _ok([_escrow_dict(e) for e in es])


# ═════════════════════════════════════════════════════════════════════════════
#  WALLET — WITHDRAWALS
# ═════════════════════════════════════════════════════════════════════════════

def _wd_dict(w: Withdrawal) -> dict:
    return {
        'id':             w.id,
        'user_id':        w.user_id,
        'amount':         float(w.amount),
        'payout_method':  w.payout_method,
        'account_number': w.account_number,
        'status':         w.status,
        'admin_note':     w.admin_note,
        'created_at':     w.created_at.isoformat() if w.created_at else None,
    }


@talib_bp.post('/wallet/withdraw')
@jwt_required()
def request_withdrawal():
    """Body: { amount, payout_method, account_number }"""
    me = _current_user()
    d  = request.get_json(silent=True) or {}
    try:
        amount = float(d['amount'])
    except (KeyError, TypeError, ValueError):
        return _err('amount required.')
    if amount < 500: return _err('Minimum withdrawal is 500 DZD.')

    method  = d.get('payout_method', 'ccp')
    account = (d.get('account_number') or '').strip()
    if not account: return _err('Account number required.')

    wallet = Wallet.query.filter_by(user_id=me.id).first()
    if not wallet or wallet.balance < amount:
        return _err('Insufficient balance.')

    # Hold funds immediately
    wallet.balance -= amount
    wallet.updated_at = datetime.utcnow()

    wd = Withdrawal(user_id=me.id, amount=amount,
                    payout_method=method, account_number=account,
                    status='pending')
    db.session.add(wd)
    db.session.add(Transaction(user_id=me.id, type='withdraw',
                               amount=amount, status='pending'))
    db.session.commit()
    return _created(_wd_dict(wd))


@talib_bp.get('/wallet/withdrawals')
@jwt_required()
def get_withdrawals():
    me = _current_user()
    ws = Withdrawal.query.filter_by(user_id=me.id).order_by(
        Withdrawal.created_at.desc()).all()
    return _ok([_wd_dict(w) for w in ws])


# ═════════════════════════════════════════════════════════════════════════════
#  ADMIN — USERS
# ═════════════════════════════════════════════════════════════════════════════

def _admin_required():
    me = _current_user()
    if not me or me.role != 'Admin':
        return None
    return me


@talib_bp.get('/admin/users')
@jwt_required()
def admin_get_users():
    if not _admin_required(): return _err('Admin only.', HTTP_403)
    users = (User.query.filter(User.role != 'Admin')
             .order_by(User.created_at.desc()).all())
    return _ok([_user_dict(u) for u in users])


@talib_bp.post('/admin/users/<int:uid>/ban')
@jwt_required()
def admin_ban(uid):
    if not _admin_required(): return _err('Admin only.', HTTP_403)
    d      = request.get_json(silent=True) or {}
    reason = d.get('reason', 'Banned by admin.')
    user   = User.query.get(uid)
    if not user: return _err('User not found.', HTTP_404)
    user.is_banned  = True
    user.ban_reason = reason
    db.session.commit()
    return _ok(_user_dict(user))


@talib_bp.post('/admin/users/<int:uid>/unban')
@jwt_required()
def admin_unban(uid):
    if not _admin_required(): return _err('Admin only.', HTTP_403)
    user = User.query.get(uid)
    if not user: return _err('User not found.', HTTP_404)
    user.is_banned  = False
    user.ban_reason = None
    db.session.commit()
    return _ok(_user_dict(user))


@talib_bp.post('/admin/users/<int:uid>/warn')
@jwt_required()
def admin_warn(uid):
    if not _admin_required(): return _err('Admin only.', HTTP_403)
    user = User.query.get(uid)
    if not user: return _err('User not found.', HTTP_404)
    user.warnings = (user.warnings or 0) + 1
    auto_banned   = False
    if user.warnings >= 3:
        user.is_banned  = True
        user.ban_reason = 'Automatically banned after 3 warnings.'
        auto_banned     = True
    db.session.commit()
    return _ok({**_user_dict(user), 'auto_banned': auto_banned})


# ═════════════════════════════════════════════════════════════════════════════
#  ADMIN — WITHDRAWALS
# ═════════════════════════════════════════════════════════════════════════════

@talib_bp.get('/admin/withdrawals')
@jwt_required()
def admin_get_withdrawals():
    if not _admin_required(): return _err('Admin only.', HTTP_403)
    ws = Withdrawal.query.order_by(Withdrawal.created_at.asc()).all()

    def wd_full(w):
        user = User.query.get(w.user_id)
        d    = _wd_dict(w)
        d['user'] = {'id': user.id, 'firstname': user.firstname,
                     'lastname': user.lastname, 'email': user.email,
                     'image': user.image} if user else None
        return d
    return _ok([wd_full(w) for w in ws])


@talib_bp.post('/admin/withdrawals/<int:wid>/approve')
@jwt_required()
def admin_approve_withdrawal(wid):
    if not _admin_required(): return _err('Admin only.', HTTP_403)
    wd = Withdrawal.query.get(wid)
    if not wd: return _err('Not found.', HTTP_404)
    if wd.status != 'pending': return _err('Already processed.')

    d = request.get_json(silent=True) or {}
    wd.status     = 'approved'
    wd.admin_note = d.get('note')

    # Mark the pending TX as completed
    tx = Transaction.query.filter_by(user_id=wd.user_id,
                                     type='withdraw', status='pending').first()
    if tx: tx.status = 'completed'
    db.session.commit()
    return _ok(_wd_dict(wd))


@talib_bp.post('/admin/withdrawals/<int:wid>/reject')
@jwt_required()
def admin_reject_withdrawal(wid):
    if not _admin_required(): return _err('Admin only.', HTTP_403)
    wd = Withdrawal.query.get(wid)
    if not wd: return _err('Not found.', HTTP_404)
    if wd.status != 'pending': return _err('Already processed.')

    d = request.get_json(silent=True) or {}
    wd.status     = 'rejected'
    wd.admin_note = d.get('note')

    # Refund the held balance
    wallet = Wallet.query.filter_by(user_id=wd.user_id).first()
    if wallet:
        wallet.balance   += wd.amount
        wallet.updated_at = datetime.utcnow()

    tx = Transaction.query.filter_by(user_id=wd.user_id,
                                     type='withdraw', status='pending').first()
    if tx: tx.status = 'failed'
    db.session.add(Transaction(user_id=wd.user_id, type='refund',
                               amount=wd.amount, status='completed'))
    db.session.commit()
    return _ok(_wd_dict(wd))


# ═════════════════════════════════════════════════════════════════════════════
#  ADMIN — EVENTS / ANNOUNCEMENTS (create / hide)
# ═════════════════════════════════════════════════════════════════════════════

@talib_bp.post('/admin/events')
@jwt_required()
def admin_create_event():
    if not _admin_required(): return _err('Admin only.', HTTP_403)
    d = request.get_json(silent=True) or {}
    e = Event(
        title       = d.get('title', ''),
        description = d.get('description', ''),
        image       = d.get('image'),
        location    = d.get('location'),
        start_at    = datetime.fromisoformat(d['start_at']) if d.get('start_at') else None,
        end_at      = datetime.fromisoformat(d['end_at'])   if d.get('end_at')   else None,
        event_type  = d.get('event_type', 'other'),
        capacity    = d.get('capacity'),
        is_visible  = True,
    )
    db.session.add(e); db.session.commit()

    # Notify all users
    try:
        users = User.query.filter(User.role != 'Admin',
                                  User.is_banned == False).all()
        for u in users:
            if u.email:
                _send_event_email(u, e)
    except Exception:
        pass

    return _created(_event_dict(e))


def _send_event_email(user: User, event: Event):
    html = f"""<html><body style="font-family:Cairo,sans-serif;background:#F5F3FF;padding:32px;">
    <div style="max-width:520px;margin:0 auto;background:#fff;border-radius:18px;
                box-shadow:0 8px 32px rgba(26,10,46,0.1);overflow:hidden;">
      <div style="background:linear-gradient(135deg,#3B0F8C,#7C3AED);padding:40px;text-align:center;">
        <span style="background:rgba(217,119,6,0.2);border:1px solid #D97706;border-radius:100px;
                     padding:4px 18px;font-size:10px;letter-spacing:0.18em;
                     text-transform:uppercase;color:#D97706;display:inline-block;margin-bottom:14px;">
          New Event
        </span>
        <h1 style="color:#fff;margin:0;font-size:24px;">{event.title}</h1>
      </div>
      <div style="padding:36px;">
        <p style="font-size:15px;color:#444;line-height:1.8;">
          Dear {user.firstname},<br/><br/>
          {event.description or ''}
        </p>
        <table style="background:#F5F3FF;border-radius:12px;padding:18px;width:100%;border-collapse:collapse;">
          <tr><td style="padding:8px;color:#5B21B6;font-weight:700;">📅 Start</td>
              <td style="padding:8px;">{event.start_at.strftime('%A, %B %d %Y at %H:%M') if event.start_at else '—'}</td></tr>
          <tr><td style="padding:8px;color:#5B21B6;font-weight:700;">📍 Location</td>
              <td style="padding:8px;">{event.location or '—'}</td></tr>
        </table>
      </div>
    </div></body></html>"""
    _send_email(user.email, f'New Event: {event.title} — {PLATFORM_NAME}', html)


@talib_bp.post('/admin/announcements')
@jwt_required()
def admin_create_announcement():
    if not _admin_required(): return _err('Admin only.', HTTP_403)
    me = _current_user()
    d  = request.get_json(silent=True) or {}
    a  = Announcement(
        title      = d.get('title', ''),
        content    = d.get('content', ''),
        image      = d.get('image'),
        is_pinned  = d.get('is_pinned', False),
        is_visible = True,
        author_id  = me.id,
    )
    db.session.add(a); db.session.commit()
    return _created(_ann_dict(a))
