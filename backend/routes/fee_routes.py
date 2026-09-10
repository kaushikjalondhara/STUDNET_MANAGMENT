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
