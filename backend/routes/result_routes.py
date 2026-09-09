from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity
from middleware.auth_middleware import teacher_required, student_required, validate_standard
from models.result_model import (
    get_results_by_standard, create_result, update_result,
    delete_result, get_student_results, DEFAULT_SUBJECTS
)

result_bp = Blueprint('results', __name__)

@result_bp.route('', methods=['GET'])
@teacher_required
def list_results():
    std_param = request.args.get('standard')
    if not std_param:
        return jsonify({'success': False, 'error': 'standard query parameter is required.'}), 400
    std, err = validate_standard(std_param)
    if err:
        return err
    results = get_results_by_standard(std)
    return jsonify({
        'success': True,
        'standard': std,
        'results': results,
        'count': len(results),
        'default_subjects': DEFAULT_SUBJECTS
    })

@result_bp.route('', methods=['POST'])
@teacher_required
def add_result():
    data = request.get_json(silent=True) or {}
    if not data.get('student_id'):
        return jsonify({'success': False, 'error': 'Student selection is required.'}), 400
    if not data.get('standard'):
        return jsonify({'success': False, 'error': 'Standard is required.'}), 400
    
    std, err = validate_standard(data['standard'])
    if err:
        return err
    data['standard'] = std

    # Check for subjects array
    subjects = data.get('subjects', [])
    if not subjects and data.get('subject'):
        subjects = [{
            'subject': data.get('subject'),
            'marks': data.get('marks', 0),
            'max_marks': data.get('max_marks', 100)
        }]
    
    if not subjects:
        return jsonify({'success': False, 'error': 'Please enter marks for at least one subject.'}), 400

    data['subjects'] = subjects

    try:
        result = create_result(data)
        
        # Send targeted notification to student
        from models.notification_model import create_notification
        create_notification(
            type_name='result',
            title=f'📝 Result Published: {result.get("exam_name", "Exam")}',
            message=f'Your marksheet has been published with grade {result.get("grade")}. Score: {result.get("percentage")}%',
            student_id=str(result.get("student_id")),
            link='result.html'
        )

        return jsonify({'success': True, 'result': result}), 201
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@result_bp.route('/<result_id>', methods=['PUT'])
@teacher_required
def edit_result(result_id):
    data = request.get_json(silent=True) or {}
    result = update_result(result_id, data)
    if not result:
        return jsonify({'success': False, 'error': 'Result not found.'}), 404
    return jsonify({'success': True, 'result': result})

@result_bp.route('/<result_id>', methods=['DELETE'])
@teacher_required
def remove_result(result_id):
    if not delete_result(result_id):
        return jsonify({'success': False, 'error': 'Result not found.'}), 404
    return jsonify({'success': True, 'message': 'Result deleted successfully.'})

@result_bp.route('/my', methods=['GET'])
@student_required
def my_results():
    student_id = get_jwt_identity()
    data = get_student_results(student_id)
    return jsonify({'success': True, **data})
