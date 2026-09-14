from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from middleware.auth_middleware import teacher_required
from models.notice_model import get_notices, create_notice, delete_notice

notice_bp = Blueprint('notices', __name__)

@notice_bp.route('', methods=['GET'])
@jwt_required()
def list_notices():
    from flask_jwt_extended import get_jwt_identity
    claims = get_jwt()
    standard = request.args.get('standard')
    role = claims.get('role')
    
    student_id = None
    if role == 'student':
        if not standard:
            standard = claims.get('standard')
        student_id = get_jwt_identity()
    
    notices = get_notices(standard, student_id)
    return jsonify({'success': True, 'notices': notices, 'count': len(notices)})

@notice_bp.route('', methods=['POST'])
@teacher_required
def add_notice():
    data = request.get_json(silent=True) or {}
    if not data.get('title'):
        return jsonify({'success': False, 'error': 'Notice title is required.'}), 400
    
    claims = get_jwt()
    data['posted_by'] = claims.get('name', 'Teacher')
    notice = create_notice(data)

    # Broadcast notification to students
    from models.notification_model import create_notification
    from datetime import datetime
    today_str = datetime.utcnow().strftime("%d-%m-%Y")
    msg_text = notice.get('content') or notice.get('description') or notice.get('title', '')
    create_notification(
        type_name='notice',
        title=f'📢 Notice: {notice.get("title")}',
        message=f'📅 તારીખ / Date: {today_str} — {msg_text[:120]}',
        standard=notice.get('standard'),
        link='notices.html'
    )

    return jsonify({'success': True, 'notice': notice}), 201

@notice_bp.route('/<notice_id>', methods=['DELETE'])
@jwt_required()
def remove_notice(notice_id):
    from flask_jwt_extended import get_jwt_identity
    from models.notice_model import hide_notice_for_student
    claims = get_jwt()
    if claims.get('role') == 'student':
        student_id = get_jwt_identity()
        if not hide_notice_for_student(notice_id, student_id):
            return jsonify({'success': False, 'error': 'Notice not found.'}), 404
        return jsonify({'success': True, 'message': 'Notice hidden successfully.'})
    else:
        if not delete_notice(notice_id):
            return jsonify({'success': False, 'error': 'Notice not found.'}), 404
        return jsonify({'success': True, 'message': 'Notice deleted successfully.'})
