# ══════════════════════════════════════════════════════════════════════════════
#  validators.py  —  Talib-Awn · طالب عون
#  Comprehensive input validation for all API endpoints
# ══════════════════════════════════════════════════════════════════════════════

import re
from typing import Any, Optional, Tuple, List
from datetime import datetime
from decimal import Decimal, InvalidOperation


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


class Validator:
    """Base validator class with common validation methods."""
    
    # Valid domains for students/employers
    VALID_DOMAINS = [
        'intelligence artificielle',
        'developpement web',
        'cyber securite',
        'reseaux et telecommunications',
        'systemes embarques',
        'science des donnees',
        'genie logiciel',
        'autre',
    ]
    
    # Valid grades for students
    VALID_GRADES = [
        'Student',
        'Professor',
        'Researcher',
        'Company manager',
    ]
    
    # Valid user types
    VALID_USER_TYPES = ['student', 'employer', 'admin', 'user']
    
    # Valid project statuses
    VALID_PROJECT_STATUSES = ['open', 'in_progress', 'completed', 'closed']
    
    # Valid event types
    VALID_EVENT_TYPES = ['workshop', 'webinar', 'seminar', 'conference', 'hackathon', 'other']
    
    # Valid transaction types
    VALID_TRANSACTION_TYPES = ['deposit', 'escrow', 'release', 'refund', 'withdraw']
    
    # Valid transaction statuses
    VALID_TRANSACTION_STATUSES = ['pending', 'completed', 'failed']
    
    # Valid escrow statuses
    VALID_ESCROW_STATUSES = ['held', 'released', 'cancelled']
    
    # Valid withdrawal statuses
    VALID_WITHDRAWAL_STATUSES = ['pending', 'approved', 'rejected']
    
    # Valid payout methods
    VALID_PAYOUT_METHODS = ['ccp', 'edahabia', 'baridimob']
    
    @staticmethod
    def validate_required(value: Any, field_name: str) -> Any:
        """Validate that a field is not empty."""
        if value is None or (isinstance(value, str) and not value.strip()):
            raise ValidationError(f'{field_name} is required.')
        return value
    
    @staticmethod
    def validate_string(value: Any, field_name: str, min_length: int = 0, 
                       max_length: int = 1000, required: bool = True) -> str:
        """Validate string field with length constraints."""
        if not value and required:
            raise ValidationError(f'{field_name} is required.')
        
        if not value and not required:
            return ''
        
        if not isinstance(value, str):
            value = str(value)
        
        value = value.strip()
        
        if len(value) < min_length:
            raise ValidationError(f'{field_name} must be at least {min_length} characters.')
        
        if len(value) > max_length:
            raise ValidationError(f'{field_name} exceeds maximum length of {max_length} characters.')
        
        return value
    
    @staticmethod
    def validate_email(email: str) -> str:
        """Validate email format."""
        if not email:
            raise ValidationError('Email is required.')
        
        email = email.strip().lower()
        
        # Email regex pattern
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            raise ValidationError('Invalid email format.')
        
        if len(email) > 120:
            raise ValidationError('Email too long (max 120 characters).')
        
        return email
    
    @staticmethod
    def validate_password(password: str, min_length: int = 8) -> str:
        """Validate password strength."""
        if not password:
            raise ValidationError('Password is required.')
        
        if len(password) < min_length:
            raise ValidationError(f'Password must be at least {min_length} characters.')
        
        if len(password) > 128:
            raise ValidationError('Password too long (max 128 characters).')
        
        # Must contain at least one letter
        if not re.search(r'[a-zA-Z]', password):
            raise ValidationError('Password must contain at least one letter.')
        
        # Must contain at least one number
        if not re.search(r'[0-9]', password):
            raise ValidationError('Password must contain at least one number.')
        
        return password
    
    @staticmethod
    def validate_phone(phone: str, required: bool = False) -> Optional[str]:
        """Validate Algerian phone number format."""
        if not phone:
            if required:
                raise ValidationError('Phone number is required.')
            return None
        
        # Remove common separators
        clean = re.sub(r'[\s\-\(\)]', '', phone)
        
        # Algerian phone patterns
        patterns = [
            r'^0[567]\d{8}$',      # Mobile
            r'^0[1-9]\d{8}$',      # Landline
            r'^\+213[567]\d{8}$',  # International mobile
            r'^00213[567]\d{8}$',  # International mobile (00)
        ]
        
        for pattern in patterns:
            if re.match(pattern, clean):
                return phone.strip()
        
        raise ValidationError('Invalid phone number. Use Algerian format (e.g., 0555123456).')
    
    @staticmethod
    def validate_integer(value: Any, field_name: str, min_value: Optional[int] = None,
                        max_value: Optional[int] = None, required: bool = True) -> Optional[int]:
        """Validate integer field."""
        if value is None:
            if required:
                raise ValidationError(f'{field_name} is required.')
            return None
        
        try:
            int_value = int(value)
        except (TypeError, ValueError):
            raise ValidationError(f'{field_name} must be a valid integer.')
        
        if min_value is not None and int_value < min_value:
            raise ValidationError(f'{field_name} must be at least {min_value}.')
        
        if max_value is not None and int_value > max_value:
            raise ValidationError(f'{field_name} must not exceed {max_value}.')
        
        return int_value
    
    @staticmethod
    def validate_decimal(value: Any, field_name: str, min_value: Optional[float] = None,
                        max_value: Optional[float] = None, precision: int = 2) -> Decimal:
        """Validate decimal/money field."""
        if value is None:
            raise ValidationError(f'{field_name} is required.')
        
        try:
            decimal_value = Decimal(str(value))
        except (TypeError, ValueError, InvalidOperation):
            raise ValidationError(f'{field_name} must be a valid number.')
        
        # Round to specified precision
        decimal_value = round(decimal_value, precision)
        
        if min_value is not None and decimal_value < Decimal(str(min_value)):
            raise ValidationError(f'{field_name} must be at least {min_value}.')
        
        if max_value is not None and decimal_value > Decimal(str(max_value)):
            raise ValidationError(f'{field_name} must not exceed {max_value}.')
        
        return decimal_value
    
    @staticmethod
    def validate_boolean(value: Any, field_name: str, required: bool = False) -> bool:
        """Validate boolean field."""
        if value is None:
            if required:
                raise ValidationError(f'{field_name} is required.')
            return False
        
        if isinstance(value, bool):
            return value
        
        # Handle string representations
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes')
        
        return bool(value)
    
    @staticmethod
    def validate_choice(value: Any, field_name: str, choices: List[str], 
                       required: bool = True, default: Optional[str] = None) -> str:
        """Validate that value is one of allowed choices."""
        if not value:
            if required and default is None:
                raise ValidationError(f'{field_name} is required.')
            return default or ''
        
        value = str(value).strip().lower()
        
        # Normalize choices to lowercase for comparison
        choices_lower = [c.lower() for c in choices]
        
        if value not in choices_lower:
            raise ValidationError(
                f'{field_name} must be one of: {", ".join(choices)}. Got: {value}'
            )
        
        # Return the original case from choices
        idx = choices_lower.index(value)
        return choices[idx]
    
    @staticmethod
    def validate_datetime(value: Any, field_name: str, required: bool = True) -> Optional[datetime]:
        """Validate datetime field."""
        if not value:
            if required:
                raise ValidationError(f'{field_name} is required.')
            return None
        
        if isinstance(value, datetime):
            return value
        
        # Try parsing ISO format
        try:
            return datetime.fromisoformat(str(value).replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            raise ValidationError(f'{field_name} must be a valid ISO datetime format.')
    
    @staticmethod
    def validate_url(url: str, required: bool = False) -> Optional[str]:
        """Validate URL format."""
        if not url:
            if required:
                raise ValidationError('URL is required.')
            return None
        
        url = url.strip()
        
        pattern = r'^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$'
        
        if not re.match(pattern, url):
            raise ValidationError('Invalid URL format.')
        
        if len(url) > 2048:
            raise ValidationError('URL too long (max 2048 characters).')
        
        return url
    
    @staticmethod
    def sanitize_html(text: str) -> str:
        """Basic HTML sanitization."""
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


# Pre-configured validators for common use cases

def validate_user_registration(data: dict) -> dict:
    """Validate user registration data."""
    v = Validator()
    
    validated = {
        'email': v.validate_email(data.get('email')),
        'password': v.validate_password(data.get('password')),
        'firstname': v.validate_string(data.get('firstname'), 'First name', min_length=2, max_length=80),
        'lastname': v.validate_string(data.get('lastname', ''), 'Last name', min_length=0, max_length=80, required=False),
        'phone': v.validate_phone(data.get('phone'), required=False),
        'type': v.validate_choice(data.get('type', 'student'), 'User type', ['student', 'employer'], default='student'),
    }
    
    # Type-specific validation
    if validated['type'] == 'student':
        validated['grade'] = v.validate_choice(data.get('grade', 'Student'), 'Grade', v.VALID_GRADES, default='Student')
        validated['domain'] = v.validate_choice(data.get('domain', 'autre'), 'Domain', v.VALID_DOMAINS, default='autre')
        validated['institution'] = v.validate_string(data.get('institution', ''), 'Institution', required=False, max_length=120)
        validated['field_of_study'] = v.validate_string(data.get('field_of_study', ''), 'Field of study', required=False, max_length=120)
        validated['student_id_number'] = v.validate_string(data.get('student_id_number', ''), 'Student ID', required=False, max_length=60)
    else:
        validated['company_name'] = v.validate_string(data.get('company_name', ''), 'Company name', required=False, max_length=120)
        validated['domain'] = v.validate_choice(data.get('domain', 'autre'), 'Domain', v.VALID_DOMAINS, default='autre')
    
    return validated


def validate_project_data(data: dict) -> dict:
    """Validate project creation/update data."""
    v = Validator()
    
    validated = {
        'title': v.validate_string(data.get('title'), 'Title', min_length=3, max_length=200),
        'description': v.validate_string(data.get('description', ''), 'Description', required=False, max_length=5000),
        'category': v.validate_string(data.get('category', 'autre'), 'Category', required=False, max_length=60),
        'status': v.validate_choice(data.get('status', 'open'), 'Status', v.VALID_PROJECT_STATUSES, default='open'),
    }
    
    # Image is optional but validate if provided
    if data.get('image'):
        validated['image'] = v.validate_string(data.get('image'), 'Image', required=False, max_length=10000)
    
    return validated


def validate_amount(amount: Any, min_amount: float = 0.0, max_amount: Optional[float] = None) -> Decimal:
    """Validate monetary amount."""
    v = Validator()
    return v.validate_decimal(amount, 'Amount', min_value=min_amount, max_value=max_amount, precision=2)
