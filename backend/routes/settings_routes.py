from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from middleware.auth_middleware import teacher_required
from models.settings_model import (
    verify_management_password, is_valid_management_token,
    change_management_password, get_school_settings,
    update_school_settings, get_standard_fee_config
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

@settings_bp.route('/public', methods=['GET'])
def get_public_school_info():
    """Publicly accessible institutional settings (school name, branding, fees, payment)."""
    settings = get_school_settings()
    payment_settings = get_payment_settings()
    school_info = settings.get('school_info', {})
    academic_year = settings.get('academic', {}).get('academic_year') or school_info.get('academic_year', '2026-2027')
    fee_cfg = settings.get('fees', {})

    return jsonify({
        'success': True,
        'school_info': school_info,
        'academic_year': academic_year,
        'standards': settings.get('academic', {}).get('standards', []),
        'subjects': settings.get('academic', {}).get('subjects', []),
        'exam_types': settings.get('academic', {}).get('exam_types', []),
        'fee_types': fee_cfg.get('fee_types', []),
        'standard_fees': fee_cfg.get('standard_fees', {}),
        'due_date': fee_cfg.get('due_date', '2026-10-31'),
        'payment_settings': payment_settings,
        'general': settings.get('general', {})
    })
