from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from middleware.auth_middleware import student_required, teacher_required, validate_standard
from models.notification_model import (
    create_notification, get_student_notifications,
    mark_notification_read, mark_all_notifications_read, get_unread_count
)

notification_bp = Blueprint('notifications', __name__)

@notification_bp.route('/my', methods=['GET'])
@student_required
def my_notifications():
    student_id = get_jwt_identity()
    claims = get_jwt()
    standard = claims.get('standard', 1)
    
    notifications = get_student_notifications(student_id, standard)
    unread = get_unread_count(student_id, standard)
    print(f"  📋 Notifications query: student_id={student_id}, standard={standard}, found={len(notifications)}, unread={unread}")
    return jsonify({
        'success': True,
        'notifications': notifications,
        'unread_count': unread
    })

@notification_bp.route('/unread-count', methods=['GET'])
@student_required
def unread_count():
    student_id = get_jwt_identity()
    claims = get_jwt()
    standard = claims.get('standard', 1)
    
    count = get_unread_count(student_id, standard)
    return jsonify({'success': True, 'unread_count': count})

@notification_bp.route('/read/<id>', methods=['PUT'])
@student_required
def read_one(id):
    student_id = get_jwt_identity()
    ok = mark_notification_read(id, student_id)
    return jsonify({'success': True, 'modified': ok})

@notification_bp.route('/read-all', methods=['PUT'])
@student_required
def read_all():
    student_id = get_jwt_identity()
    claims = get_jwt()
    standard = claims.get('standard', 1)
    count = mark_all_notifications_read(student_id, standard)
    return jsonify({'success': True, 'count': count})

@notification_bp.route('/send', methods=['POST'])
@teacher_required
def send_notification():
    data = request.get_json(silent=True) or {}
    type_name = data.get('type', 'general')
    title = data.get('title')
    message = data.get('message')
    standard = data.get('standard')
    student_id = data.get('student_id')
    link = data.get('link')

    if not title or not message:
        return jsonify({'success': False, 'error': 'Title and message are required.'}), 400

    notif = create_notification(type_name, title, message, standard, student_id, link)
    return jsonify({'success': True, 'notification': notif, 'message': 'Notification sent successfully.'}), 201
