import jwt
from functools import wraps
from datetime import datetime, timedelta, timezone
from flask import request, jsonify
from config import Config

def generate_token(user_id, role, extra_data=None):
    """Generates a JWT access token valid for the configured expiry hours."""
    now = datetime.now(timezone.utc)
    payload = {
        'sub': str(user_id),
        'role': role,
        'iat': now,
        'exp': now + timedelta(hours=Config.JWT_ACCESS_TOKEN_EXPIRES_HOURS)
    }
    if extra_data and isinstance(extra_data, dict):
        payload.update(extra_data)
        
    token = jwt.encode(payload, Config.JWT_SECRET_KEY, algorithm='HS256')
    return token

def decode_token(token):
    """Decodes and validates a JWT token."""
    try:
        payload = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def token_required(f):
    """Decorator ensuring a valid JWT is provided in the Authorization header."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'success': False, 'message': 'Authorization header is missing'}), 401

        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return jsonify({'success': False, 'message': 'Invalid token format. Expected: Bearer <token>'}), 401

        token = parts[1]
        payload = decode_token(token)
        if not payload:
            return jsonify({'success': False, 'message': 'Token is invalid or has expired'}), 401

        sub = payload.get('sub')
        user_id = int(sub) if sub and str(sub).isdigit() else sub

        request.user = {
            'id': user_id,
            'role': payload.get('role'),
            'name': payload.get('name'),
            'email': payload.get('email'),
            'roll_number': payload.get('roll_number')
        }
        return f(*args, **kwargs)
    return decorated

def teacher_required(f):
    """Decorator restricting endpoint to authenticated teachers."""
    @wraps(f)
    @token_required
    def decorated(*args, **kwargs):
        if request.user.get('role') != 'teacher':
            return jsonify({'success': False, 'message': 'Access restricted to teachers only'}), 403
        return f(*args, **kwargs)
    return decorated

def student_required(f):
    """Decorator restricting endpoint to authenticated students."""
    @wraps(f)
    @token_required
    def decorated(*args, **kwargs):
        if request.user.get('role') != 'student':
            return jsonify({'success': False, 'message': 'Access restricted to students only'}), 403
        return f(*args, **kwargs)
    return decorated
