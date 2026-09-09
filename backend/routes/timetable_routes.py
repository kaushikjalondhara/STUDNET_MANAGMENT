from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from middleware.auth_middleware import teacher_required, validate_standard
from models.timetable_model import get_timetable, save_timetable

timetable_bp = Blueprint('timetable', __name__)

@timetable_bp.route('', methods=['GET'])
@jwt_required()
def view_timetable():
    claims = get_jwt()
    std_param = request.args.get('standard')
    if not std_param and claims.get('role') == 'student':
        std_param = claims.get('standard')

    if not std_param:
        return jsonify({'success': False, 'error': 'standard is required.'}), 400

    std, err = validate_standard(std_param)
    if err:
        return err

    tt = get_timetable(std)
    return jsonify({'success': True, 'timetable': tt})

@timetable_bp.route('', methods=['POST'])
@teacher_required
def update_timetable():
    data = request.get_json(silent=True) or {}
    if not data.get('standard') or not data.get('schedule'):
        return jsonify({'success': False, 'error': 'Standard and schedule are required.'}), 400

    std, err = validate_standard(data['standard'])
    if err:
        return err

    tt = save_timetable(std, data['schedule'])
    return jsonify({'success': True, 'timetable': tt, 'message': 'Timetable updated successfully.'})
