# ══════════════════════════════════════════════════════════════════════════════
#  parsers.py  —  Talib-Awn · طالب عون
#  Simple request-body helpers (no flask-restful dependency needed).
# ══════════════════════════════════════════════════════════════════════════════
from flask import request


def get_json():
    """Return parsed JSON body or empty dict (never raises)."""
    return request.get_json(silent=True) or {}


def require_fields(data: dict, *fields):
    """
    Check that all required field names exist and are non-empty.
    Returns (ok: bool, missing_field_name | None).
    """
    for f in fields:
        if not data.get(f):
            return False, f
    return True, None


def str_field(data: dict, key: str, default: str = '') -> str:
    return str(data.get(key) or default).strip()


def int_field(data: dict, key: str, default: int = 0) -> int:
    try:
        return int(data.get(key, default))
    except (TypeError, ValueError):
        return default


def float_field(data: dict, key: str, default: float = 0.0) -> float:
    try:
        return float(data.get(key, default))
    except (TypeError, ValueError):
        return default


def bool_field(data: dict, key: str, default: bool = False) -> bool:
    v = data.get(key, default)
    if isinstance(v, bool):
        return v
    return str(v).lower() in ('1', 'true', 'yes')
