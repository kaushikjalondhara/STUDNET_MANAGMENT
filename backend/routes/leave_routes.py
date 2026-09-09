from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity, get_jwt
from middleware.auth_middleware import teacher_required, student_required, validate_standard
from models.leave_model import (
    get_leaves_by_standard, get_student_leaves,
    apply_leave, update_leave_status
)

leave_bp = Blueprint('leaves', __name__)

@leave_bp.route('', methods=['GET'])
@teacher_required
def list_standard_leaves():
    std_param = request.args.get('standard')
    if not std_param:
        return jsonify({'success': False, 'error': 'standard is required.'}), 400
    
    std, err = validate_standard(std_param)
    if err:
        return err

    leaves = get_leaves_by_standard(std)
    return jsonify({'success': True, 'standard': std, 'leaves': leaves, 'count': len(leaves)})

@leave_bp.route('/my', methods=['GET'])
@student_required
def my_leaves():
    student_id = get_jwt_identity()
    leaves = get_student_leaves(student_id)
    return jsonify({'success': True, 'leaves': leaves, 'count': len(leaves)})

@leave_bp.route('/apply', methods=['POST'])
@student_required
def submit_leave():
    student_id = get_jwt_identity()
    claims = get_jwt()
    standard = claims.get('standard', 5)
    data = request.get_json(silent=True) or {}

    if not data.get('from_date') or not data.get('to_date') or not data.get('reason'):
        return jsonify({'success': False, 'error': 'From Date, To Date and Reason are required.'}), 400

    leave = apply_leave(student_id, standard, data)
    return jsonify({'success': True, 'leave': leave, 'message': 'Leave application submitted successfully.'}), 201

@leave_bp.route('/<leave_id>/status', methods=['PUT'])
@teacher_required
def change_leave_status(leave_id):
    data = request.get_json(silent=True) or {}
    status = data.get('status', 'Approved')
    remark = data.get('remark', '')

    updated = update_leave_status(leave_id, status, remark)
    if not updated:
        return jsonify({'success': False, 'error': 'Leave record not found.'}), 404
    
    # Send targeted notification to student
    from models.notification_model import create_notification
    status_icon = '✅' if status == 'Approved' else '❌'
    create_notification(
        type_name='leave',
        title=f'📨 Leave Request {status} {status_icon}',
        message=f'Your leave application from {updated.get("from_date")} to {updated.get("to_date")} has been {status}. Teacher Remark: {remark or "None"}',
        student_id=str(updated.get("student_id")),
        link='leave.html'
    )

    return jsonify({'success': True, 'leave': updated, 'message': f'Leave status marked as {status}.'})
