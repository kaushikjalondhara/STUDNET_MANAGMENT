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


# ─── Excel Export for Attendance ─────────────────────────────────────────────

import io
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from flask import send_file

@report_bp.route('/attendance/export', methods=['GET'])
@teacher_required
def export_attendance_report():
    """Exports attendance report of a standard to Excel (.xlsx)."""
    std_param = request.args.get('standard')
    if not std_param:
        return jsonify({'success': False, 'error': 'standard is required.'}), 400
    std, err = validate_standard(std_param)
    if err:
        return err

    students = get_students_by_standard(std)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"Std {std} Attendance"

    # Title Banner
    ws.merge_cells('A1:G1')
    t = ws.cell(row=1, column=1)
    t.value = f"EDUMANAGE PRO - STANDARD {std} ATTENDANCE SUMMARY"
    t.font = Font(name="Arial", size=13, bold=True, color="FFFFFF")
    t.fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
    t.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 30

    headers = ["Roll No", "Student Name", "Mobile", "Total Days", "Present Days", "Absent Days", "Attendance %"]
    ws.append(headers)
    ws.row_dimensions[2].height = 24

    header_font = Font(name="Arial", size=10, bold=True, color="1E3A8A")
    header_fill = PatternFill(start_color="E0E7FF", end_color="E0E7FF", fill_type="solid")
    border_thin = Border(
        left=Side(style='thin', color='E5E7EB'),
        right=Side(style='thin', color='E5E7EB'),
        top=Side(style='thin', color='D1D5DB'),
        bottom=Side(style='thin', color='D1D5DB')
    )

    for col_num in range(1, len(headers) + 1):
        c = ws.cell(row=2, column=col_num)
        c.font = header_font
        c.fill = header_fill
        c.alignment = Alignment(horizontal="center", vertical="center")
        c.border = border_thin

    row_font = Font(name="Arial", size=10)
    alt_fill = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")

    for idx, s in enumerate(students, start=3):
        att = get_student_attendance(s['_id'])
        ws.append([
            s.get('roll_no', ''),
            s.get('name', ''),
            s.get('mobile') or '—',
            att.get('total', 0),
            att.get('present', 0),
            att.get('absent', 0),
            f"{att.get('attendance_pct', 0)}%"
        ])
        ws.row_dimensions[idx].height = 20
        use_fill = (idx % 2 == 0)

        for col_num in range(1, 8):
            c = ws.cell(row=idx, column=col_num)
            c.font = row_font
            c.border = border_thin
            if use_fill:
                c.fill = alt_fill
            if col_num in [1, 3, 4, 5, 6, 7]:
                c.alignment = Alignment(horizontal="center", vertical="center")
            else:
                c.alignment = Alignment(horizontal="left", vertical="center")

    widths = [12, 28, 18, 14, 14, 14, 16]
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = w

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name=f"attendance_standard_{std}.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

