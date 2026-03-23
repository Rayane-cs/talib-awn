# ══════════════════════════════════════════════════════════════════════════════
#  auth_utils.py  —  Talib-Awn · طالب عون
#  Enhanced authentication utilities with rate limiting and security
# ══════════════════════════════════════════════════════════════════════════════

import time
import re
from typing import Optional, Dict, Tuple
from functools import wraps
from flask import request, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from models import db, User

# Rate limiting stores: {ip_or_email: [timestamp1, timestamp2, ...]}
_rate_limit_login: Dict[str, list] = {}
_rate_limit_otp: Dict[str, list] = {}
_rate_limit_api: Dict[str, list] = {}

# Configuration
RATE_LIMIT_LOGIN_MAX = 5  # 5 attempts
RATE_LIMIT_LOGIN_WINDOW = 300  # 5 minutes
RATE_LIMIT_OTP_MAX = 3  # 3 OTP requests
RATE_LIMIT_OTP_WINDOW = 180  # 3 minutes
RATE_LIMIT_API_MAX = 100  # 100 requests
RATE_LIMIT_API_WINDOW = 60  # 1 minute


def _clean_rate_limit(store: dict, window: int):
    """Remove expired timestamps from rate limit store."""
    now = time.time()
    for key in list(store.keys()):
        store[key] = [ts for ts in store[key] if now - ts < window]
        if not store[key]:
            del store[key]


def check_rate_limit(store: dict, key: str, max_attempts: int, window: int) -> Tuple[bool, Optional[str]]:
    """
    Check if rate limit is exceeded.
    Returns (allowed: bool, error_message: Optional[str])
    """
    _clean_rate_limit(store, window)
    
    if key not in store:
        store[key] = []
    
    attempts = store[key]
    if len(attempts) >= max_attempts:
        wait_time = int(window - (time.time() - attempts[0]))
        return False, f'Too many attempts. Try again in {wait_time} seconds.'
    
    store[key].append(time.time())
    return True, None


def rate_limit_login(func):
    """Decorator for login endpoint rate limiting."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Use IP + email combination for login
        ip = request.remote_addr
        data = request.get_json(silent=True) or {}
        email = data.get('email', '').lower()
        key = f"{ip}:{email}" if email else ip
        
        allowed, error = check_rate_limit(_rate_limit_login, key, 
                                          RATE_LIMIT_LOGIN_MAX, 
                                          RATE_LIMIT_LOGIN_WINDOW)
        if not allowed:
            return jsonify({'ok': False, 'error': error}), 429
        
        return func(*args, **kwargs)
    return wrapper


def rate_limit_otp(func):
    """Decorator for OTP endpoint rate limiting."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Use IP for OTP requests
        ip = request.remote_addr
        
        allowed, error = check_rate_limit(_rate_limit_otp, ip, 
                                          RATE_LIMIT_OTP_MAX, 
                                          RATE_LIMIT_OTP_WINDOW)
        if not allowed:
            return jsonify({'ok': False, 'error': error}), 429
        
        return func(*args, **kwargs)
    return wrapper


def rate_limit_api(func):
    """Decorator for general API rate limiting."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Use IP for general API calls
        ip = request.remote_addr
        
        allowed, error = check_rate_limit(_rate_limit_api, ip, 
                                          RATE_LIMIT_API_MAX, 
                                          RATE_LIMIT_API_WINDOW)
        if not allowed:
            return jsonify({'ok': False, 'error': error}), 429
        
        return func(*args, **kwargs)
    return wrapper


def validate_email(email: str) -> Tuple[bool, Optional[str]]:
    """
    Validate email format.
    Returns (valid: bool, error_message: Optional[str])
    """
    if not email or len(email) < 3:
        return False, 'Email is required.'
    
    # Basic email regex
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        return False, 'Invalid email format.'
    
    if len(email) > 120:
        return False, 'Email too long (max 120 characters).'
    
    return True, None


def validate_password(password: str) -> Tuple[bool, Optional[str]]:
    """
    Validate password strength.
    Returns (valid: bool, error_message: Optional[str])
    """
    if not password:
        return False, 'Password is required.'
    
    if len(password) < 8:
        return False, 'Password must be at least 8 characters long.'
    
    if len(password) > 128:
        return False, 'Password too long (max 128 characters).'
    
    # Check for at least one letter and one number
    if not re.search(r'[a-zA-Z]', password):
        return False, 'Password must contain at least one letter.'
    
    if not re.search(r'[0-9]', password):
        return False, 'Password must contain at least one number.'
    
    return True, None


def validate_phone(phone: str) -> Tuple[bool, Optional[str]]:
    """
    Validate Algerian phone number.
    Returns (valid: bool, error_message: Optional[str])
    """
    if not phone:
        return True, None  # Phone is optional
    
    # Remove spaces and common separators
    clean_phone = re.sub(r'[\s\-\(\)]', '', phone)
    
    # Algerian phone patterns:
    # - Mobile: 05XX XX XX XX or 06XX XX XX XX or 07XX XX XX XX
    # - Landline: 0XX XX XX XX XX (where XX is area code)
    # - International: +213 XXX XX XX XX or 00213 XXX XX XX XX
    
    patterns = [
        r'^0[567]\d{8}$',  # Mobile without spaces
        r'^0[1-9]\d{8}$',  # Landline without spaces
        r'^\+213[567]\d{8}$',  # International mobile
        r'^00213[567]\d{8}$',  # International mobile (00 prefix)
    ]
    
    for pattern in patterns:
        if re.match(pattern, clean_phone):
            return True, None
    
    return False, 'Invalid phone number format. Use Algerian format (e.g., 0555123456).'


def validate_name(name: str, field_name: str = 'Name') -> Tuple[bool, Optional[str]]:
    """
    Validate name fields (firstname, lastname).
    Returns (valid: bool, error_message: Optional[str])
    """
    if not name or not name.strip():
        return False, f'{field_name} is required.'
    
    if len(name) < 2:
        return False, f'{field_name} must be at least 2 characters.'
    
    if len(name) > 80:
        return False, f'{field_name} too long (max 80 characters).'
    
    # Allow letters (including Arabic), spaces, hyphens, apostrophes
    # Fixed regex: removed \w which includes digits and underscore
    if not re.match(r'^[a-zA-Z\s\u0600-\u06FF\'\-]+$', name.strip()):
        return False, f'{field_name} contains invalid characters.'
    
    return True, None


def sanitize_input(text: str, max_length: int = 1000) -> str:
    """
    Sanitize user input to prevent XSS and injection attacks.
    """
    if not text:
        return ''
    
    # Trim to max length
    text = str(text)[:max_length]
    
    # Remove null bytes
    text = text.replace('\x00', '')
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    return text


def get_current_user_safe() -> Optional[User]:
    """
    Safely get current authenticated user.
    Returns User instance or None if not authenticated/not found.
    """
    try:
        verify_jwt_in_request()
        uid = get_jwt_identity()
        if not uid:
            return None
        user = db.session.get(User, uid)
        return user
    except Exception:
        return None


def require_user(func):
    """
    Decorator that ensures user is authenticated.
    Returns 401 if not authenticated.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        user = get_current_user_safe()
        if not user:
            return jsonify({'ok': False, 'error': 'Authentication required.'}), 401
        return func(*args, user=user, **kwargs)
    return wrapper


def require_admin(func):
    """
    Decorator that ensures user is admin.
    Returns 403 if not admin.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        user = get_current_user_safe()
        if not user:
            return jsonify({'ok': False, 'error': 'Authentication required.'}), 401
        if user.type != 'admin':
            return jsonify({'ok': False, 'error': 'Admin access required.'}), 403
        return func(*args, user=user, **kwargs)
    return wrapper


def check_user_banned(user: User) -> Tuple[bool, Optional[str]]:
    """
    Check if user is banned.
    Returns (is_banned: bool, ban_reason: Optional[str])
    """
    if user.is_banned:
        reason = user.ban_reason or 'Your account has been suspended.'
        return True, reason
    return False, None


def sanitize_html_simple(text: str) -> str:
    """
    Simple HTML sanitization - escapes common HTML tags.
    For rich text, consider using bleach library.
    """
    if not text:
        return ''
    
    replacements = {
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#x27;',
        '/': '&#x2F;',
    }
    
    for char, escape in replacements.items():
        text = text.replace(char, escape)
    
    return text


def validate_url(url: str) -> Tuple[bool, Optional[str]]:
    """
    Basic URL validation.
    Returns (valid: bool, error_message: Optional[str])
    """
    if not url:
        return True, None  # URLs are often optional
    
    # Basic URL pattern
    url_pattern = r'^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$'
    
    if not re.match(url_pattern, url):
        return False, 'Invalid URL format.'
    
    if len(url) > 2048:
        return False, 'URL too long.'
    
    return True, None
