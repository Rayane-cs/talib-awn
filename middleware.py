# ══════════════════════════════════════════════════════════════════════════════
#  middleware.py  —  Talib-Awn · طالب عون
#  Request/response middleware for logging, validation, and error handling
# ══════════════════════════════════════════════════════════════════════════════

import time
import traceback
from functools import wraps
from flask import request, jsonify, g
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from validators import ValidationError
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def log_request():
    """Log incoming request details."""
    g.start_time = time.time()
    logger.info(f"➡️  {request.method} {request.path} from {request.remote_addr}")


def log_response(response):
    """Log outgoing response details."""
    if hasattr(g, 'start_time'):
        duration = time.time() - g.start_time
        logger.info(f"⬅️  {request.method} {request.path} - Status: {response.status_code} - Duration: {duration:.3f}s")
    return response


def handle_errors(func):
    """
    Decorator for comprehensive error handling.
    Catches and formats errors consistently.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        
        except ValidationError as e:
            # Validation errors (400 Bad Request)
            logger.warning(f"Validation error: {str(e)}")
            return jsonify({
                'ok': False,
                'error': str(e),
                'type': 'validation_error'
            }), 400
        
        except IntegrityError as e:
            # Database integrity errors (409 Conflict)
            logger.error(f"Database integrity error: {str(e)}")
            
            # Parse common integrity errors
            error_msg = 'Database constraint violation.'
            if 'Duplicate entry' in str(e):
                error_msg = 'This record already exists.'
            elif 'foreign key constraint' in str(e).lower():
                error_msg = 'Referenced record does not exist.'
            
            return jsonify({
                'ok': False,
                'error': error_msg,
                'type': 'integrity_error'
            }), 409
        
        except SQLAlchemyError as e:
            # Other database errors (500 Internal Server Error)
            logger.error(f"Database error: {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({
                'ok': False,
                'error': 'Database error occurred. Please try again.',
                'type': 'database_error'
            }), 500
        
        except PermissionError as e:
            # Permission errors (403 Forbidden)
            logger.warning(f"Permission error: {str(e)}")
            return jsonify({
                'ok': False,
                'error': str(e),
                'type': 'permission_error'
            }), 403
        
        except ValueError as e:
            # Value errors (400 Bad Request)
            logger.warning(f"Value error: {str(e)}")
            return jsonify({
                'ok': False,
                'error': str(e),
                'type': 'value_error'
            }), 400
        
        except Exception as e:
            # Unexpected errors (500 Internal Server Error)
            logger.error(f"Unexpected error: {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({
                'ok': False,
                'error': 'An unexpected error occurred. Please try again.',
                'type': 'server_error'
            }), 500
    
    return wrapper


def validate_json(func):
    """
    Decorator to ensure request has valid JSON body.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if request.method in ['POST', 'PUT', 'PATCH']:
            if not request.is_json:
                return jsonify({
                    'ok': False,
                    'error': 'Content-Type must be application/json',
                    'type': 'invalid_content_type'
                }), 400
            
            data = request.get_json(silent=True)
            if data is None:
                return jsonify({
                    'ok': False,
                    'error': 'Invalid JSON in request body',
                    'type': 'invalid_json'
                }), 400
        
        return func(*args, **kwargs)
    
    return wrapper


def require_fields(*required_fields):
    """
    Decorator to validate that required fields are present in request JSON.
    
    Usage:
        @require_fields('email', 'password')
        def login():
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            data = request.get_json(silent=True) or {}
            missing = []
            
            for field in required_fields:
                if field not in data or not data[field]:
                    missing.append(field)
            
            if missing:
                return jsonify({
                    'ok': False,
                    'error': f'Missing required fields: {", ".join(missing)}',
                    'type': 'missing_fields',
                    'missing_fields': missing
                }), 400
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def paginate(default_limit: int = 50, max_limit: int = 200):
    """
    Decorator to add pagination support to endpoints.
    Adds 'page' and 'limit' parameters to g context.
    
    Usage:
        @paginate(default_limit=20, max_limit=100)
        def get_items():
            page = g.page
            limit = g.limit
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                page = max(1, int(request.args.get('page', 1)))
            except ValueError:
                page = 1
            
            try:
                limit = min(max_limit, max(1, int(request.args.get('limit', default_limit))))
            except ValueError:
                limit = default_limit
            
            g.page = page
            g.limit = limit
            g.offset = (page - 1) * limit
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def cache_control(max_age: int = 0, public: bool = False):
    """
    Decorator to add cache control headers to responses.
    
    Usage:
        @cache_control(max_age=300, public=True)
        def get_public_data():
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            response = func(*args, **kwargs)
            
            # If response is a tuple (data, status_code)
            if isinstance(response, tuple):
                data, status_code = response
                headers = {}
            else:
                data = response
                status_code = 200
                headers = {}
            
            cache_directive = 'public' if public else 'private'
            headers['Cache-Control'] = f'{cache_directive}, max-age={max_age}'
            
            if isinstance(data, dict):
                return jsonify(data), status_code, headers
            else:
                return data, status_code, headers
        
        return wrapper
    return decorator


def cors_preflight(func):
    """
    Decorator to handle CORS preflight requests.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if request.method == 'OPTIONS':
            response = jsonify({'ok': True})
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            response.headers['Access-Control-Max-Age'] = '3600'
            return response
        
        return func(*args, **kwargs)
    
    return wrapper


class RequestLogger:
    """Context manager for detailed request logging."""
    
    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        logger.info(f"🔵 Starting: {self.operation_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        
        if exc_type is None:
            logger.info(f"✅ Completed: {self.operation_name} ({duration:.3f}s)")
        else:
            logger.error(f"❌ Failed: {self.operation_name} ({duration:.3f}s) - {exc_val}")
        
        return False  # Don't suppress exceptions


def api_response(data=None, message: str = None, status: int = 200):
    """
    Standardized API response format.
    
    Args:
        data: Response data (dict, list, or None)
        message: Optional message
        status: HTTP status code
    
    Returns:
        Flask response tuple (json, status_code)
    """
    response = {'ok': status < 400}
    
    if data is not None:
        response['data'] = data
    
    if message:
        response['message'] = message
    
    return jsonify(response), status


def api_error(error: str, status: int = 400, error_type: str = None):
    """
    Standardized API error response.
    
    Args:
        error: Error message
        status: HTTP status code
        error_type: Optional error type identifier
    
    Returns:
        Flask response tuple (json, status_code)
    """
    response = {
        'ok': False,
        'error': error
    }
    
    if error_type:
        response['type'] = error_type
    
    return jsonify(response), status


# Export commonly used functions
__all__ = [
    'log_request',
    'log_response',
    'handle_errors',
    'validate_json',
    'require_fields',
    'paginate',
    'cache_control',
    'cors_preflight',
    'RequestLogger',
    'api_response',
    'api_error',
]
