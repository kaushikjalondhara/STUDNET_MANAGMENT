from flask import Blueprint, request, jsonify
from middleware.auth_middleware import teacher_required, validate_standard
from models.student_model import count_by_standard
from models.attendance_model import get_today_stats, get_attendance_summary
from models.result_model import class_average

teacher_bp = Blueprint('teacher', __name__)

@teacher_bp.route('/standards', methods=['GET'])
@teacher_required
def get_all_standards():
    """Overview of all 12 standards — used on the Select Standard page."""
    standards = []
    for std in range(1, 13):
        count = count_by_standard(std)
        standards.append({
            'standard': std,
            'label': f'Standard {std}',
            'total_students': count
        })
    return jsonify({'success': True, 'standards': standards})

@teacher_bp.route('/dashboard', methods=['GET'])
@teacher_required
def dashboard():
    """Dashboard stats for a specific standard."""
    std_param = request.args.get('standard')
    if not std_param:
        return jsonify({'success': False, 'error': 'standard query parameter is required.'}), 400
    std, err = validate_standard(std_param)
    if err:
        return err

    date_param = request.args.get('date')
    total_students = count_by_standard(std)
    today_stats = get_today_stats(std, date_param)
    attendance_summary = get_attendance_summary(std)
    avg_score = class_average(std)

    total_present = today_stats['present_today']
    total_absent = today_stats['absent_today']
    att_pct = attendance_summary.get('avg_attendance_pct', 0)

    return jsonify({
        'success': True,
        'standard': std,
        'label': f'Standard {std}',
        'stats': {
            'total_students': total_students,
            'present_today': total_present,
            'absent_today': total_absent,
            'not_marked': max(0, total_students - total_present - total_absent),
            'attendance_pct': att_pct,
            'class_average': avg_score
        }
    })
