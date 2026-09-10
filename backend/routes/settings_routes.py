from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from middleware.auth_middleware import teacher_required
from models.settings_model import (
    verify_management_password, is_valid_management_token,
    change_management_password, get_school_settings,
    update_school_settings, get_standard_fee_config,
    get_standard_hall_ticket_config, update_standard_hall_ticket_config,
    copy_hall_ticket_config_to_all
)
from models.fee_model import get_payment_settings

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/verify-password', methods=['POST'])
@teacher_required
def verify_password():
    data = request.get_json(silent=True) or {}
    password = data.get('password', '')
    if not password:
        return jsonify({'success': False, 'error': 'Management password is required.'}), 400

    ok, res = verify_management_password(password)
    if ok:
        return jsonify({
            'success': True,
            'message': 'Management authorization verified.',
            'management_token': res
        })
    else:
        return jsonify({'success': False, 'error': res}), 401

@settings_bp.route('/change-password', methods=['POST'])
@teacher_required
def change_password():
    data = request.get_json(silent=True) or {}
    old_pw = data.get('old_password', '')
    new_pw = data.get('new_password', '')
    confirm_pw = data.get('confirm_password', '')

    if not old_pw or not new_pw:
        return jsonify({'success': False, 'error': 'Both old and new passwords are required.'}), 400

    if new_pw != confirm_pw:
        return jsonify({'success': False, 'error': 'New password and confirmation do not match.'}), 400

    ok, msg = change_management_password(old_pw, new_pw)
    if ok:
        return jsonify({'success': True, 'message': msg})
    else:
        return jsonify({'success': False, 'error': msg}), 400

@settings_bp.route('', methods=['GET'])
@teacher_required
def get_all_settings():
    settings = get_school_settings()
    return jsonify({'success': True, 'settings': settings})

@settings_bp.route('/public', methods=['GET'])
def get_public_school_info():
    """Public endpoint to fetch current school branding and info without auth."""
    settings = get_school_settings()
    school_info = settings.get('school_info', {})
    fees = settings.get('fees', {})
    return jsonify({
        'success': True,
        'school_info': school_info,
        'academic_year': settings.get('academic', {}).get('academic_year', '2026-2027'),
        'payment_settings': {
            'upi_id': fees.get('upi_id'),
            'payee_name': fees.get('payee_name', school_info.get('name')),
            'merchant_name': fees.get('merchant_name', school_info.get('name')),
            'razorpay_key_id': fees.get('razorpay_key_id'),
            'enable_upi': fees.get('enable_upi', True),
            'enable_razorpay': fees.get('enable_razorpay', True)
        }
    }), 200

@settings_bp.route('/<category>', methods=['PUT', 'POST'])
@teacher_required
def update_category(category):
    # Check management token in header or body
    mgmt_token = request.headers.get('X-Management-Token') or (request.get_json(silent=True) or {}).get('management_token')
    if not is_valid_management_token(mgmt_token):
        return jsonify({'success': False, 'error': 'Management authorization required. Please verify management password.'}), 403

    data = request.get_json(silent=True) or {}
    if 'management_token' in data:
        data = {k: v for k, v in data.items() if k != 'management_token'}

    try:
        updated = update_school_settings(category, data)
        return jsonify({
            'success': True,
            'message': f'School settings for [{category}] updated successfully.',
            'settings': updated
        })
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': f'Failed to update settings: {str(e)}'}), 500

@settings_bp.route('/fee-config/<int:standard>', methods=['GET'])
@teacher_required
def get_fee_config(standard):
    cfg = get_standard_fee_config(standard)
    return jsonify({'success': True, 'standard': standard, 'fee_config': cfg})

@settings_bp.route('/hall-ticket/<int:standard>', methods=['GET'])
@jwt_required()
def get_hall_ticket(standard):
    """Fetch hall ticket configuration and timetable for a specific standard (student or teacher)."""
    cfg = get_standard_hall_ticket_config(standard)
    return jsonify({'success': True, 'standard': standard, 'config': cfg})

@settings_bp.route('/hall-ticket/<int:standard>', methods=['PUT', 'POST'])
@teacher_required
def update_hall_ticket(standard):
    """Update hall ticket schedule and publish status for a specific standard."""
    mgmt_token = request.headers.get('X-Management-Token') or (request.get_json(silent=True) or {}).get('management_token')
    if not is_valid_management_token(mgmt_token):
        return jsonify({'success': False, 'error': 'Management authorization required. Please verify management password.'}), 403

    data = request.get_json(silent=True) or {}
    updated = update_standard_hall_ticket_config(standard, data)
    return jsonify({
        'success': True,
        'message': f'Hall ticket configuration saved for Standard {standard}.',
        'standard': standard,
        'config': updated
    })

@settings_bp.route('/hall-ticket/copy-all', methods=['POST'])
@teacher_required
def copy_hall_ticket_all():
    """Copy a standard's hall ticket schedule to all other standards (1-12)."""
    mgmt_token = request.headers.get('X-Management-Token') or (request.get_json(silent=True) or {}).get('management_token')
    if not is_valid_management_token(mgmt_token):
        return jsonify({'success': False, 'error': 'Management authorization required.'}), 403

    data = request.get_json(silent=True) or {}
    source_std = data.get('source_standard', 1)
    res = copy_hall_ticket_config_to_all(source_std)
    return jsonify(res)

