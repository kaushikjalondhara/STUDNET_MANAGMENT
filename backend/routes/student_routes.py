from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity, get_jwt
from middleware.auth_middleware import teacher_required, student_required, validate_standard
from models.student_model import (
    get_students_by_standard, get_student_by_id,
    create_student, update_student, delete_student
)
from pymongo.errors import DuplicateKeyError

student_bp = Blueprint('students', __name__)

@student_bp.route('', methods=['GET'])
@teacher_required
def list_students():
    std_param = request.args.get('standard')
    if not std_param:
        return jsonify({'success': False, 'error': 'standard query parameter is required.'}), 400
    std, err = validate_standard(std_param)
    if err:
        return err
    students = get_students_by_standard(std)
    return jsonify({'success': True, 'standard': std, 'students': students, 'count': len(students)})

@student_bp.route('/<student_id>', methods=['GET'])
@teacher_required
def get_student(student_id):
    student = get_student_by_id(student_id)
    if not student:
        return jsonify({'success': False, 'error': 'Student not found.'}), 404
    return jsonify({'success': True, 'student': student})

@student_bp.route('', methods=['POST'])
@teacher_required
def add_student():
    data = request.get_json(silent=True) or {}
    required = ['name', 'roll_no', 'standard', 'password']
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({'success': False, 'error': f"Missing fields: {', '.join(missing)}"}), 400

    std, err = validate_standard(data['standard'])
    if err:
        return err
    data['standard'] = std

    try:
        student = create_student(data)
        return jsonify({'success': True, 'student': student}), 201
    except DuplicateKeyError as e:
        key = 'roll number' if 'roll_no' in str(e) else 'email'
        return jsonify({'success': False, 'error': f'A student with that {key} already exists.'}), 409

@student_bp.route('/<student_id>', methods=['PUT'])
@teacher_required
def edit_student(student_id):
    data = request.get_json(silent=True) or {}
    student = get_student_by_id(student_id)
    if not student:
        return jsonify({'success': False, 'error': 'Student not found.'}), 404
    try:
        updated = update_student(student_id, data)
        return jsonify({'success': True, 'student': updated})
    except DuplicateKeyError as e:
        key = 'roll number' if 'roll_no' in str(e) else 'email'
        return jsonify({'success': False, 'error': f'A student with that {key} already exists.'}), 409

@student_bp.route('/<student_id>', methods=['DELETE'])
@teacher_required
def remove_student(student_id):
    if not get_student_by_id(student_id):
        return jsonify({'success': False, 'error': 'Student not found.'}), 404
    delete_student(student_id)
    return jsonify({'success': True, 'message': 'Student deleted successfully.'})

@student_bp.route('/me', methods=['GET'])
@student_required
def my_profile():
    student_id = get_jwt_identity()
    student = get_student_by_id(student_id)
    if not student:
        return jsonify({'success': False, 'error': 'Student not found.'}), 404
    return jsonify({'success': True, 'student': student})
