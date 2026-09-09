from flask import Blueprint, request, jsonify
from middleware.auth_middleware import teacher_required, validate_standard
from models.student_model import get_students_by_standard
from models.attendance_model import get_attendance_history, get_student_attendance
from models.result_model import get_results_by_standard, class_average
from models.fee_model import get_standard_fee_summary
from database.db import get_db

report_bp = Blueprint('reports', __name__)

@report_bp.route('/attendance', methods=['GET'])
@teacher_required
def attendance_report():
    std_param = request.args.get('standard')
    if not std_param:
        return jsonify({'success': False, 'error': 'standard is required.'}), 400
    std, err = validate_standard(std_param)
    if err:
        return err

    students = get_students_by_standard(std)
    history = get_attendance_history(std, limit=30)
    
    # Per student attendance percentage
    student_stats = []
    for s in students:
        att = get_student_attendance(s['_id'])
        student_stats.append({
            'student_id': s['_id'],
            'name': s['name'],
            'roll_no': s['roll_no'],
            'total_days': att['total'],
            'present_days': att['present'],
            'absent_days': att['absent'],
            'attendance_pct': att['attendance_pct']
        })

    return jsonify({
        'success': True,
        'standard': std,
        'total_students': len(students),
        'history': history,
        'students': student_stats
    })

@report_bp.route('/results', methods=['GET'])
@teacher_required
def result_report():
    std_param = request.args.get('standard')
    if not std_param:
        return jsonify({'success': False, 'error': 'standard is required.'}), 400
    std, err = validate_standard(std_param)
    if err:
        return err

    results = get_results_by_standard(std)
    avg_score = class_average(std)

    # Calculate toppers and grade distribution
    sorted_results = sorted(results, key=lambda r: float(r.get('percentage', 0)), reverse=True)
    pass_count = sum(1 for r in results if r.get('status') == 'Pass')
    fail_count = sum(1 for r in results if r.get('status') == 'Fail')

    return jsonify({
        'success': True,
        'standard': std,
        'total_results': len(results),
        'class_average': avg_score,
        'pass_count': pass_count,
        'fail_count': fail_count,
        'results': sorted_results
    })

@report_bp.route('/analytics', methods=['GET'])
@teacher_required
def analytics_data():
    std_param = request.args.get('standard')
    if not std_param:
        return jsonify({'success': False, 'error': 'standard is required.'}), 400
    std, err = validate_standard(std_param)
    if err:
        return err

    students = get_students_by_standard(std)
    fee_summary = get_standard_fee_summary(std)
    results = get_results_by_standard(std)
    att_history = get_attendance_history(std, limit=14)

    return jsonify({
        'success': True,
        'standard': std,
        'total_students': len(students),
        'fee_summary': fee_summary,
        'results_count': len(results),
        'class_average': class_average(std),
        'attendance_trend': att_history
    })
