from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from middleware.auth_middleware import teacher_required, validate_standard
from models.homework_model import get_homework_by_standard, create_homework, delete_homework

homework_bp = Blueprint('homework', __name__)

@homework_bp.route('', methods=['GET'])
@jwt_required()
def list_homework():
    claims = get_jwt()
    std_param = request.args.get('standard')
    if not std_param and claims.get('role') == 'student':
        std_param = claims.get('standard')
    
    if not std_param:
        return jsonify({'success': False, 'error': 'standard is required.'}), 400
    
    std, err = validate_standard(std_param)
    if err:
        return err

    hw_list = get_homework_by_standard(std)
    return jsonify({'success': True, 'standard': std, 'homework': hw_list, 'count': len(hw_list)})

@homework_bp.route('', methods=['POST'])
@teacher_required
def add_homework():
    data = request.get_json(silent=True) or {}
    if not data.get('standard') or not data.get('title'):
        return jsonify({'success': False, 'error': 'Standard and title are required.'}), 400
    
    std, err = validate_standard(data['standard'])
    if err:
        return err
    data['standard'] = std

    hw = create_homework(data)
    
    # Broadcast notification to students in standard
    from models.notification_model import create_notification
    from datetime import datetime
    today_str = datetime.utcnow().strftime("%d-%m-%Y")
    due_str = data.get("due_date", "Soon")
    create_notification(
        type_name='homework',
        title=f'📚 New Homework: {data.get("subject", "General")}',
        message=f'📅 Assigned on: {today_str} | ⏰ Due: {due_str} — {data["title"]}',
        standard=std,
        link='homework.html'
    )

    return jsonify({'success': True, 'homework': hw}), 201

@homework_bp.route('/<hw_id>', methods=['DELETE'])
@teacher_required
def remove_homework(hw_id):
    if not delete_homework(hw_id):
        return jsonify({'success': False, 'error': 'Homework not found.'}), 404
    return jsonify({'success': True, 'message': 'Homework deleted successfully.'})
