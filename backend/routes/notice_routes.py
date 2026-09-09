from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from middleware.auth_middleware import teacher_required
from models.notice_model import get_notices, create_notice, delete_notice

notice_bp = Blueprint('notices', __name__)

@notice_bp.route('', methods=['GET'])
@jwt_required()
def list_notices():
    claims = get_jwt()
    standard = request.args.get('standard')
    if not standard and claims.get('role') == 'student':
        standard = claims.get('standard')
    
    notices = get_notices(standard)
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
    msg_text = notice.get('content') or notice.get('description') or notice.get('title', '')
    create_notification(
        type_name='notice',
        title=f'📢 Notice: {notice.get("title")}',
        message=f'New notice published: {msg_text[:120]}',
        standard=notice.get('standard'),
        link='notices.html'
    )

    return jsonify({'success': True, 'notice': notice}), 201

@notice_bp.route('/<notice_id>', methods=['DELETE'])
@teacher_required
def remove_notice(notice_id):
    if not delete_notice(notice_id):
        return jsonify({'success': False, 'error': 'Notice not found.'}), 404
    return jsonify({'success': True, 'message': 'Notice deleted successfully.'})
