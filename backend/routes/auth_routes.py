from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from models.teacher_model import find_teacher_by_email, verify_teacher_password
from models.student_model import find_student_by_mobile, verify_student_password
import re

auth_bp = Blueprint('auth', __name__)

# ─── Teacher Login ────────────────────────────────────────────────────────────

@auth_bp.route('/teacher/login', methods=['POST'])
def teacher_login():
    data = request.get_json(silent=True) or {}
    email    = data.get('email', '').strip()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'success': False, 'error': 'Email and password are required.'}), 400

    teacher = find_teacher_by_email(email)
    if not teacher or not verify_teacher_password(teacher, password):
        return jsonify({'success': False, 'error': 'Invalid email or password.'}), 401

    token = create_access_token(
        identity=str(teacher['_id']),
        additional_claims={'role': 'teacher', 'name': teacher['name']}
    )
    return jsonify({
        'success': True,
        'token': token,
        'teacher': {
            'id': str(teacher['_id']),
            'name': teacher['name'],
            'email': teacher['email']
        }
    })

# ─── Student Login (mobile + password) ───────────────────────────────────────

MOBILE_RE = re.compile(r'^[6-9]\d{9}$')

@auth_bp.route('/student/login', methods=['POST'])
def student_login():
    data = request.get_json(silent=True) or {}
    mobile   = data.get('mobile', '').strip()
    password = data.get('password', '')

    # Validate mobile
    if not mobile:
        return jsonify({'success': False, 'error': 'Mobile number is required.'}), 400
    if not MOBILE_RE.match(mobile):
        return jsonify({'success': False, 'error': 'Enter a valid 10-digit Indian mobile number.'}), 400
    if not password:
        return jsonify({'success': False, 'error': 'Password is required.'}), 400

    student = find_student_by_mobile(mobile)
    if not student or not verify_student_password(student, password):
        return jsonify({'success': False, 'error': 'Invalid mobile number or password.'}), 401

    token = create_access_token(
        identity=str(student['_id']),
        additional_claims={
            'role': 'student',
            'name': student['name'],
            'standard': student['standard']
        }
    )
    return jsonify({
        'success': True,
        'token': token,
        'student': {
            'id':       str(student['_id']),
            'name':     student['name'],
            'roll_no':  student.get('roll_no'),
            'standard': student['standard'],
            'mobile':   mobile
        }
    })
