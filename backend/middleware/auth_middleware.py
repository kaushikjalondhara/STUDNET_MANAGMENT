from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt

def teacher_required(fn):
    """Decorator: JWT required + role must be 'teacher'."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 401
        claims = get_jwt()
        if claims.get('role') != 'teacher':
            return jsonify({'success': False, 'error': 'Teacher access required.'}), 403
        return fn(*args, **kwargs)
    return wrapper

def student_required(fn):
    """Decorator: JWT required + role must be 'student'."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 401
        claims = get_jwt()
        if claims.get('role') != 'student':
            return jsonify({'success': False, 'error': 'Student access required.'}), 403
        return fn(*args, **kwargs)
    return wrapper

def validate_standard(standard_value) -> tuple:
    """
    Validate that a standard value is an integer 1-12.
    Supports integers, strings like '2', or strings like 'Standard 2'.
    Returns (int_value, None) on success, (None, error_response) on failure.
    """
    try:
        import re
        if isinstance(standard_value, str):
            m = re.search(r'\d+', standard_value)
            std = int(m.group()) if m else int(standard_value)
        else:
            std = int(standard_value)

        if not (1 <= std <= 12):
            raise ValueError()
        return std, None
    except (TypeError, ValueError):
        return None, (
            jsonify({'success': False, 'error': 'Standard must be an integer between 1 and 12.'}),
            400
        )

