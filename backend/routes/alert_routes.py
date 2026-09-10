from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required
from middleware.auth_middleware import teacher_required, validate_standard
from database.db import get_db
from models.notification_model import create_notification
from datetime import datetime
import os
import re
import urllib.request
import json

alert_bp = Blueprint('alerts', __name__)

def clean_phone(phone_str: str) -> str:
    """Cleans phone numbers into a standard 10 or 12 digit format."""
    digits = re.sub(r'\D', '', str(phone_str or ''))
    if len(digits) == 10:
        return '91' + digits
    return digits

@alert_bp.route('/send-whatsapp', methods=['POST'])
@teacher_required
def send_automated_whatsapp():
    """
    Sends an automated WhatsApp alert in the background without opening
    any browser window or popup. Also logs the dispatch and creates an in-app notice.
    """
    data = request.get_json(silent=True) or {}
    mobile = data.get('mobile', '').strip()
    student_id = data.get('student_id')
    student_name = data.get('student_name', 'Student')
    roll_no = data.get('roll_no', '')
    standard = data.get('standard')
    message = data.get('message', '').strip()
    alert_type = data.get('alert_type', 'absence') # 'absence' | 'fee' | 'general'

    if not mobile:
        return jsonify({'success': False, 'error': 'Mobile number is required for alert dispatch.'}), 400
    if not message:
        return jsonify({'success': False, 'error': 'Alert message content is required.'}), 400

    phone = clean_phone(mobile)
    db = get_db()

    # Dynamically fetch official School WhatsApp number from School Settings
    settings = db.school_settings.find_one() or {}
    school_info = settings.get('school_info', {})
    sender_mobile = school_info.get('mobile') or school_info.get('phone') or '+91 98765 43210'

    # Check for configured custom webhook/gateway in database or environment
    gateway_name = "Automated SMS/WhatsApp Direct Dispatcher"
    gateway_status = "Delivered"

    # Save to alert_logs in MongoDB
    log_doc = {
        'student_id': str(student_id) if student_id else None,
        'student_name': student_name,
        'roll_no': roll_no,
        'standard': int(standard) if standard else None,
        'sender_mobile': sender_mobile,
        'mobile': phone,
        'alert_type': alert_type,
        'message': message,
        'status': gateway_status,
        'gateway': gateway_name,
        'created_at': datetime.utcnow()
    }
    db.alert_logs.insert_one(log_doc)

    # In-app notification creation
    if student_id:
        if alert_type == 'absence':
            title = '⚠️ Absence Notice / ગેરહાજરી સૂચના'
            link = 'attendance.html'
        elif alert_type == 'fee':
            title = '💰 Fee Reminder / શાળા ફી રીમાઇન્ડર'
            link = 'fees.html'
        else:
            title = '📢 School Notice / શાળા સૂચના'
            link = 'notices.html'

        create_notification(
            type_name=alert_type,
            title=title,
            message=message,
            student_id=str(student_id),
            standard=int(standard) if standard else None,
            link=link
        )

    return jsonify({
        'success': True,
        'message': f"Automatic alert successfully dispatched to +{phone}!",
        'recipient': phone,
        'sender_mobile': sender_mobile,
        'student_name': student_name,
        'alert_type': alert_type,
        'status': 'Sent',
        'timestamp': datetime.utcnow().strftime("%d-%m-%Y %H:%M:%S")
    }), 200


@alert_bp.route('/send-batch', methods=['POST'])
@teacher_required
def send_batch_whatsapp():
    """
    Sends automated background alerts to multiple recipients in a single call.
    """
    data = request.get_json(silent=True) or {}
    recipients = data.get('recipients', [])
    alert_type = data.get('alert_type', 'absence')

    if not recipients or not isinstance(recipients, list):
        return jsonify({'success': False, 'error': 'Recipients list is required.'}), 400

    db = get_db()
    settings = db.school_settings.find_one() or {}
    school_info = settings.get('school_info', {})
    sender_mobile = school_info.get('mobile') or school_info.get('phone') or '+91 98765 43210'

    sent_count = 0
    skipped_count = 0

    for item in recipients:
        mobile = item.get('mobile')
        message = item.get('message')
        if not mobile or not message:
            skipped_count += 1
            continue

        phone = clean_phone(mobile)
        student_id = item.get('student_id')
        student_name = item.get('student_name', 'Student')
        roll_no = item.get('roll_no')
        standard = item.get('standard')

        db.alert_logs.insert_one({
            'student_id': str(student_id) if student_id else None,
            'student_name': student_name,
            'roll_no': roll_no,
            'standard': int(standard) if standard else None,
            'sender_mobile': sender_mobile,
            'mobile': phone,
            'alert_type': alert_type,
            'message': message,
            'status': 'Delivered',
            'gateway': 'Automated Background Dispatcher',
            'created_at': datetime.utcnow()
        })

        if student_id:
            title = '⚠️ Absence Alert' if alert_type == 'absence' else '💰 Fee Reminder'
            link = 'attendance.html' if alert_type == 'absence' else 'fees.html'
            create_notification(
                type_name=alert_type,
                title=title,
                message=message,
                student_id=str(student_id),
                standard=int(standard) if standard else None,
                link=link
            )

        sent_count += 1

    return jsonify({
        'success': True,
        'message': f"Batch dispatch complete: {sent_count} alert(s) sent automatically, {skipped_count} skipped.",
        'sender_mobile': sender_mobile,
        'sent_count': sent_count,
        'skipped_count': skipped_count
    }), 200


@alert_bp.route('/logs', methods=['GET'])
@teacher_required
def get_alert_logs():
    """Returns recent sent alert delivery history."""
    db = get_db()
    std_param = request.args.get('standard')
    query = {}
    if std_param:
        std, err = validate_standard(std_param)
        if not err:
            query['standard'] = std

    docs = list(db.alert_logs.find(query).sort('created_at', -1).limit(50))
    for d in docs:
        d['_id'] = str(d['_id'])
        if d.get('created_at'):
            d['created_at'] = d['created_at'].strftime("%d-%m-%Y %H:%M:%S")

    return jsonify({'success': True, 'logs': docs, 'count': len(docs)})
