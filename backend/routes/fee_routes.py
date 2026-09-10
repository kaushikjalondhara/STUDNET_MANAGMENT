from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from middleware.auth_middleware import student_required, teacher_required, validate_standard
from models.fee_model import (
    get_or_create_student_fee, record_fee_payment,
    get_receipt, get_standard_fee_summary,
    get_payment_settings, update_payment_settings
)
from models.notification_model import create_notification

fee_bp = Blueprint('fees', __name__)

@fee_bp.route('/settings', methods=['GET'])
@jwt_required()
def get_settings():
    settings = get_payment_settings()
    return jsonify({'success': True, 'settings': settings})

@fee_bp.route('/settings', methods=['POST'])
@teacher_required
def save_settings():
    data = request.get_json(silent=True) or {}
    settings = update_payment_settings(data)
    return jsonify({'success': True, 'message': 'Payment settings updated successfully.', 'settings': settings})

@fee_bp.route('/student', methods=['GET'])
@student_required
def student_fees():
    student_id = get_jwt_identity()
    claims = get_jwt()
    standard = claims.get('standard', 1)

    fee_info = get_or_create_student_fee(student_id, standard)
    return jsonify({'success': True, 'fee': fee_info})

@fee_bp.route('/pay', methods=['POST'])
@student_required
def pay_fee():
    student_id = get_jwt_identity()
    claims = get_jwt()
    standard = claims.get('standard', 1)

    data = request.get_json(silent=True) or {}
    amount = data.get('amount')
    payment_mode = data.get('payment_mode', 'Online UPI')
    notes = data.get('notes', '')
    utr_number = data.get('utr_number', '').strip()
    razorpay_payment_id = data.get('razorpay_payment_id', '').strip()

    if not amount or float(amount) <= 0:
        return jsonify({'success': False, 'error': 'Valid payment amount is required.'}), 400

    result = record_fee_payment(
        student_id, standard, float(amount), payment_mode, notes,
        utr_number=utr_number, razorpay_payment_id=razorpay_payment_id
    )

    # Trigger Fee Payment Success notification
    utr_msg = f" (UTR: {utr_number})" if utr_number else ""
    create_notification(
        type_name='fee',
        title='💰 Fee Payment Successful',
        message=f"₹{amount:,.0f} received successfully! Receipt #{result['transaction']['receipt_no']}{utr_msg}.",
        student_id=student_id,
        link='fees.html'
    )

    return jsonify({
        'success': True,
        'message': f"Payment of ₹{amount:,.0f} completed successfully!",
        'fee': result['fee'],
        'transaction': result['transaction']
    }), 201

@fee_bp.route('/receipt/<transaction_id>', methods=['GET'])
@jwt_required()
def view_receipt(transaction_id):
    rec = get_receipt(transaction_id)
    if not rec:
        return jsonify({'success': False, 'error': 'Receipt not found.'}), 404
    return jsonify({'success': True, 'receipt': rec})

@fee_bp.route('/standard', methods=['GET'])
@teacher_required
def standard_fees():
    std_param = request.args.get('standard')
    if not std_param:
        return jsonify({'success': False, 'error': 'standard query parameter is required.'}), 400

    std, err = validate_standard(std_param)
    if err:
        return err

    summary = get_standard_fee_summary(std)
    return jsonify({'success': True, 'summary': summary})

@fee_bp.route('/remind', methods=['POST'])
@teacher_required
def send_fee_reminder():
    data = request.get_json(silent=True) or {}
    std_param = data.get('standard')
    student_id = data.get('student_id') # Optional specific student
    due_date = data.get('due_date')
    if not due_date:
        from models.settings_model import get_school_settings
        settings = get_school_settings()
        due_date = settings.get('fees', {}).get('due_date', '31-Oct-2026')

    if not std_param:
        return jsonify({'success': False, 'error': 'standard is required.'}), 400

    std, err = validate_standard(std_param)
    if err:
        return err

    if student_id:
        create_notification(
            type_name='fee',
            title='🔔 Urgent Fee Reminder',
            message=f'Dear student, please clear your pending school fees before {due_date}.',
            student_id=student_id,
            link='fees.html'
        )
        msg = 'Fee reminder sent to student.'
    else:
        # Broadcast to all students in standard with pending fee
        create_notification(
            type_name='fee',
            title='🔔 Standard Fee Reminder',
            message=f'Dear Standard {std} students, please submit your term school fees before {due_date}.',
            standard=std,
            link='fees.html'
        )
        msg = f'Fee reminder broadcasted to all Standard {std} students.'

    return jsonify({'success': True, 'message': msg})


# ─── Excel Export for Fees ───────────────────────────────────────────────────

import io
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from flask import send_file

@fee_bp.route('/export', methods=['GET'])
@teacher_required
def export_fees():
    """Exports fee collection records of a standard to Excel (.xlsx)."""
    std_param = request.args.get('standard')
    if not std_param:
        return jsonify({'success': False, 'error': 'standard is required.'}), 400
    std, err = validate_standard(std_param)
    if err:
        return err

    summary = get_standard_fee_summary(std)
    students = summary.get('students', [])

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"Std {std} Fee Report"

    # Title Banner
    ws.merge_cells('A1:H1')
    t = ws.cell(row=1, column=1)
    t.value = f"EDUMANAGE PRO - STANDARD {std} FEE COLLECTION REPORT"
    t.font = Font(name="Arial", size=13, bold=True, color="FFFFFF")
    t.fill = PatternFill(start_color="047857", end_color="047857", fill_type="solid") # Emerald Green
    t.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 30

    # Summary Row
    ws.merge_cells('A2:H2')
    s = ws.cell(row=2, column=1)
    s.value = f"Total Expected: ₹{summary['total_expected']:,.2f}  |  Collected: ₹{summary['total_collected']:,.2f}  |  Pending: ₹{summary['total_pending']:,.2f}  |  Collection: {summary['collection_pct']}%"
    s.font = Font(name="Arial", size=10, bold=True, color="065F46")
    s.fill = PatternFill(start_color="ECFDF5", end_color="ECFDF5", fill_type="solid")
    s.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[2].height = 22

    # Headers
    headers = ["Roll No", "Student Name", "Mobile No", "Total Fee (₹)", "Paid (₹)", "Pending (₹)", "Status", "Last Payment Date"]
    ws.append(headers)
    ws.row_dimensions[3].height = 24

    header_font = Font(name="Arial", size=10, bold=True, color="047857")
    header_fill = PatternFill(start_color="D1FAE5", end_color="D1FAE5", fill_type="solid")
    border_thin = Border(
        left=Side(style='thin', color='E5E7EB'),
        right=Side(style='thin', color='E5E7EB'),
        top=Side(style='thin', color='D1D5DB'),
        bottom=Side(style='thin', color='D1D5DB')
    )

    for col_num in range(1, len(headers) + 1):
        c = ws.cell(row=3, column=col_num)
        c.font = header_font
        c.fill = header_fill
        c.alignment = Alignment(horizontal="center", vertical="center")
        c.border = border_thin

    # Data Rows
    row_font = Font(name="Arial", size=10)
    paid_fill = PatternFill(start_color="DEF7EC", end_color="DEF7EC", fill_type="solid")
    unpaid_fill = PatternFill(start_color="FDE8E8", end_color="FDE8E8", fill_type="solid")
    partial_fill = PatternFill(start_color="FEF08A", end_color="FEF08A", fill_type="solid")

    for idx, row in enumerate(students, start=4):
        ws.append([
            row.get('roll_no', ''),
            row.get('name', ''),
            row.get('mobile') or '—',
            row.get('total_fee', 0),
            row.get('paid_amount', 0),
            row.get('pending_amount', 0),
            row.get('status', 'Unpaid'),
            row.get('last_payment') or '—'
        ])
        ws.row_dimensions[idx].height = 20

        for col_num in range(1, 9):
            c = ws.cell(row=idx, column=col_num)
            c.font = row_font
            c.border = border_thin
            if col_num in [1, 3, 7, 8]:
                c.alignment = Alignment(horizontal="center", vertical="center")
            elif col_num in [4, 5, 6]:
                c.alignment = Alignment(horizontal="right", vertical="center")
                c.number_format = '₹#,##0'
            else:
                c.alignment = Alignment(horizontal="left", vertical="center")

            if col_num == 7:
                st = row.get('status', '')
                if st == 'Paid':
                    c.fill = paid_fill
                elif st == 'Partial':
                    c.fill = partial_fill
                else:
                    c.fill = unpaid_fill

    widths = [12, 28, 18, 16, 16, 16, 14, 20]
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = w

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name=f"fees_standard_{std}.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

