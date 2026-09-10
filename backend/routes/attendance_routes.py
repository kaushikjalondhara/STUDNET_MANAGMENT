from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity
from middleware.auth_middleware import teacher_required, student_required, validate_standard
from models.attendance_model import (
    get_attendance_for_date, bulk_upsert_attendance,
    get_student_attendance, get_attendance_history
)
from models.student_model import get_students_by_standard

attendance_bp = Blueprint('attendance', __name__)

# ─── Teacher: get attendance for a standard + date ────────────────────────────

@attendance_bp.route('', methods=['GET'])
@teacher_required
def get_attendance():
    std_param = request.args.get('standard')
    if not std_param:
        return jsonify({'success': False, 'error': 'standard query parameter is required.'}), 400
    std, err = validate_standard(std_param)
    if err:
        return err

    date_str = request.args.get('date')
    if not date_str:
        from datetime import date
        date_str = date.today().isoformat()

    # All students for this standard
    students = get_students_by_standard(std)
    # Existing attendance records for that date
    records  = get_attendance_for_date(std, date_str)
    record_map = {r['student_id']: r['status'] for r in records}

    attendance_list = []
    for s in students:
        attendance_list.append({
            'student_id': s['_id'],
            'name':       s['name'],
            'roll_no':    s['roll_no'],
            'mobile':     s.get('mobile', ''),
            'email':      s.get('email', ''),
            'status':     record_map.get(s['_id'], 'not_marked')
        })

    present    = sum(1 for a in attendance_list if a['status'] == 'present')
    absent     = sum(1 for a in attendance_list if a['status'] == 'absent')
    total      = len(attendance_list)
    not_marked = total - present - absent
    has_records = len(records) > 0   # ← tells frontend if this date was previously saved

    return jsonify({
        'success':     True,
        'standard':    std,
        'date':        date_str,
        'has_records': has_records,
        'attendance':  attendance_list,
        'summary': {
            'total':          total,
            'present':        present,
            'absent':         absent,
            'not_marked':     not_marked,
            'attendance_pct': round(present / total * 100, 1) if total > 0 else 0
        }
    })

# ─── Teacher: bulk save attendance ───────────────────────────────────────────

@attendance_bp.route('/bulk', methods=['POST'])
@teacher_required
def save_bulk_attendance():
    data = request.get_json(silent=True) or {}
    std_param = data.get('standard')
    if not std_param:
        return jsonify({'success': False, 'error': 'standard is required.'}), 400
    std, err = validate_standard(std_param)
    if err:
        return err

    date_str = data.get('date')
    if not date_str:
        from datetime import date
        date_str = date.today().isoformat()

    records = data.get('records', [])
    if not records:
        return jsonify({'success': False, 'error': 'records array is required.'}), 400

    count = bulk_upsert_attendance(std, date_str, records)

    # 🔔 Student Notification: "Today's attendance marked"
    from models.notification_model import create_notification
    create_notification(
        type_name='attendance',
        title='📅 Attendance Marked',
        message="Today's attendance marked",
        standard=std,
        link='attendance.html'
    )

    # Targeted alert for absent students
    for r in records:
        if r.get('status') == 'absent' and r.get('student_id'):
            create_notification(
                type_name='attendance',
                title='⚠️ Attendance Alert: Marked Absent',
                message=f"You were marked absent today ({date_str}). Please contact your class teacher.",
                student_id=str(r['student_id']),
                link='attendance.html'
            )

    return jsonify({
        'success': True,
        'message': f'Attendance saved for {count} students on {date_str}.',
        'date':    date_str
    })

# ─── Teacher: attendance history (date-wise summary) ─────────────────────────

@attendance_bp.route('/history', methods=['GET'])
@teacher_required
def get_history():
    std_param = request.args.get('standard')
    if not std_param:
        return jsonify({'success': False, 'error': 'standard query parameter is required.'}), 400
    std, err = validate_standard(std_param)
    if err:
        return err

    from datetime import date
    month_param = request.args.get('month')
    sort_param  = request.args.get('sort', 'asc')
    history = get_attendance_history(std, month=month_param, sort=sort_param)
    return jsonify({
        'success':  True,
        'standard': std,
        'month':    month_param or date.today().strftime('%Y-%m'),
        'history':  history
    })

# ─── Student: own attendance ──────────────────────────────────────────────────

@attendance_bp.route('/my', methods=['GET'])
@student_required
def my_attendance():
    student_id = get_jwt_identity()
    summary    = get_student_attendance(student_id)
    return jsonify({'success': True, **summary})
