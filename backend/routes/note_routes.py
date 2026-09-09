from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from middleware.auth_middleware import teacher_required, validate_standard
from models.note_model import create_note, get_notes_by_standard, delete_note
from models.notification_model import create_notification

note_bp = Blueprint('notes', __name__)

@note_bp.route('', methods=['GET'])
@jwt_required()
def get_notes():
    claims = get_jwt()
    role = claims.get('role', 'teacher')
    
    if role == 'student':
        std = claims.get('standard')
    else:
        std_param = request.args.get('standard')
        if not std_param:
            return jsonify({'success': False, 'error': 'standard is required.'}), 400
        std, err = validate_standard(std_param)
        if err:
            return err

    notes = get_notes_by_standard(std)
    return jsonify({'success': True, 'notes': notes, 'standard': std})

@note_bp.route('', methods=['POST'])
@teacher_required
def add_note():
    data = request.get_json(silent=True) or {}
    if not data.get('title') or not data.get('standard'):
        return jsonify({'success': False, 'error': 'Title and standard are required.'}), 400

    std, err = validate_standard(data['standard'])
    if err:
        return err
    data['standard'] = std

    claims = get_jwt()
    data['teacher_name'] = claims.get('name', 'Class Teacher')

    note = create_note(data)

    # 🔔 Student Notification: "New notes available"
    create_notification(
        type_name='notes',
        title=f'📖 New Notes: {note.get("subject", "General")}',
        message=f'New notes available: {note.get("title")}',
        standard=std,
        link='notes.html'
    )

    return jsonify({
        'success': True,
        'message': 'Study material / notes published successfully.',
        'note': note
    }), 201

@note_bp.route('/<note_id>', methods=['DELETE'])
@teacher_required
def remove_note(note_id):
    if not delete_note(note_id):
        return jsonify({'success': False, 'error': 'Note not found.'}), 404
    return jsonify({'success': True, 'message': 'Note removed successfully.'})
