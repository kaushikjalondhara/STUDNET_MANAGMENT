from database.db import get_db
from bson import ObjectId
from datetime import datetime, date
import random

DEFAULT_BREAKDOWN = [
    {'head': 'Tuition & Academic Fee', 'amount': 15000},
    {'head': 'Computer & Science Lab Fee', 'amount': 4000},
    {'head': 'Library & Digital Resources', 'amount': 2000},
    {'head': 'Sports, Yoga & Activity Fee', 'amount': 2500},
    {'head': 'Examination & Evaluation Fee', 'amount': 1500}
]
DEFAULT_TOTAL_FEE = 25000

from models.settings_model import get_standard_fee_config

def serialize(doc) -> dict:
    if doc is None:
        return None
    doc = dict(doc)
    if '_id' in doc:
        doc['_id'] = str(doc['_id'])
    if 'student_id' in doc and isinstance(doc['student_id'], ObjectId):
        doc['student_id'] = str(doc['student_id'])
    return doc

def get_or_create_student_fee(student_id: str, standard: int) -> dict:
    db = get_db()
    sid = ObjectId(student_id)
    record = db.fees.find_one({'student_id': sid})
    cfg = get_standard_fee_config(standard)
    std_total_fee = float(cfg.get('total_fee', DEFAULT_TOTAL_FEE))

    if not record:
        # Create initial fee account for student using standard's configured fees
        breakdown = cfg.get('breakdown', DEFAULT_BREAKDOWN)
        due_date = cfg.get('due_date', '2026-10-31')
        doc = {
            'student_id': sid,
            'standard': int(standard),
            'total_fee': std_total_fee,
            'paid_amount': 0,
            'pending_amount': std_total_fee,
            'status': 'Unpaid', # 'Unpaid' | 'Partial' | 'Paid'
            'due_date': due_date,
            'breakdown': breakdown,
            'transactions': [],
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        db.fees.insert_one(doc)
        record = db.fees.find_one({'student_id': sid})
    elif record.get('paid_amount', 0) == 0 and not record.get('transactions'):
        # If student hasn't paid yet, sync with standard's configured fee
        if record.get('total_fee') != std_total_fee:
            db.fees.update_one(
                {'_id': record['_id']},
                {
                    '$set': {
                        'total_fee': std_total_fee,
                        'pending_amount': std_total_fee,
                        'breakdown': cfg.get('breakdown', record.get('breakdown', DEFAULT_BREAKDOWN)),
                        'due_date': cfg.get('due_date', record.get('due_date', '2026-10-31')),
                        'updated_at': datetime.utcnow()
                    }
                }
            )
            record = db.fees.find_one({'student_id': sid})

    return serialize(record)

def record_fee_payment(student_id: str, standard: int, amount: float, payment_mode: str, notes: str = '', utr_number: str = None, razorpay_payment_id: str = None) -> dict:
    db = get_db()
    sid = ObjectId(student_id)
    fee_doc = get_or_create_student_fee(student_id, standard)

    amount = float(amount)
    current_paid = float(fee_doc.get('paid_amount', 0))
    total_fee = float(fee_doc.get('total_fee', DEFAULT_TOTAL_FEE))

    new_paid = min(total_fee, current_paid + amount)
    new_pending = max(0.0, total_fee - new_paid)
    new_status = 'Paid' if new_pending <= 0 else ('Partial' if new_paid > 0 else 'Unpaid')

    txn_id = f"TXN{datetime.utcnow().strftime('%Y%m%d%H%M%S')}{random.randint(100, 999)}"
    receipt_no = f"REC-{datetime.utcnow().year}-{random.randint(10000, 99999)}"

    # Fetch student name and roll no for receipt
    student = db.students.find_one({'_id': sid})
    student_name = student.get('name', 'Student') if student else 'Student'
    roll_no = student.get('roll_no', '—') if student else '—'

    transaction = {
        'transaction_id': txn_id,
        'receipt_no': receipt_no,
        'amount': amount,
        'payment_mode': payment_mode or 'Online UPI',
        'utr_number': utr_number or '',
        'razorpay_payment_id': razorpay_payment_id or '',
        'status': 'Success',
        'student_name': student_name,
        'roll_no': roll_no,
        'standard': int(standard),
        'notes': notes,
        'date': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
        'timestamp': datetime.utcnow()
    }

    db.fees.update_one(
        {'student_id': sid},
        {
            '$set': {
                'paid_amount': new_paid,
                'pending_amount': new_pending,
                'status': new_status,
                'updated_at': datetime.utcnow()
            },
            '$push': {'transactions': transaction}
        }
    )

    # Save to receipts collection for fast lookup
    db.receipts.insert_one(dict(transaction, student_id=sid))

    return {
        'fee': serialize(db.fees.find_one({'student_id': sid})),
        'transaction': transaction
    }

def get_receipt(transaction_id: str) -> dict:
    db = get_db()
    rec = db.receipts.find_one({'transaction_id': transaction_id})
    return serialize(rec)

def get_standard_fee_summary(standard: int) -> dict:
    db = get_db()
    students = list(db.students.find({'standard': int(standard)}))
    
    total_expected = 0
    total_collected = 0
    total_pending = 0
    paid_count = 0
    partial_count = 0
    unpaid_count = 0

    student_fee_list = []

    for s in students:
        fee = get_or_create_student_fee(str(s['_id']), standard)
        tot = fee.get('total_fee', DEFAULT_TOTAL_FEE)
        pd = fee.get('paid_amount', 0)
        pnd = fee.get('pending_amount', tot)
        st = fee.get('status', 'Unpaid')

        total_expected += tot
        total_collected += pd
        total_pending += pnd

        if st == 'Paid':
            paid_count += 1
        elif st == 'Partial':
            partial_count += 1
        else:
            unpaid_count += 1

        student_fee_list.append({
            'student_id': str(s['_id']),
            'name': s.get('name'),
            'roll_no': s.get('roll_no'),
            'total_fee': tot,
            'paid_amount': pd,
            'pending_amount': pnd,
            'status': st,
            'last_payment': fee.get('transactions', [])[-1]['date'] if fee.get('transactions') else None
        })

    collection_pct = round((total_collected / total_expected * 100), 1) if total_expected > 0 else 0

    return {
        'standard': int(standard),
        'total_students': len(students),
        'total_expected': total_expected,
        'total_collected': total_collected,
        'total_pending': total_pending,
        'collection_pct': collection_pct,
        'paid_count': paid_count,
        'partial_count': partial_count,
        'unpaid_count': unpaid_count,
        'students': student_fee_list
    }

def get_payment_settings() -> dict:
    db = get_db()
    settings = db.payment_settings.find_one({})
    if not settings:
        default_settings = {
            'upi_id': 'schoolfees@oksbi',
            'payee_name': 'EduManage Pro Public School',
            'merchant_name': 'EduManage Pro School',
            'merchant_code': '8211',
            'razorpay_key_id': 'rzp_test_1DP5mmOlF5G5ag', # Standard test key format
            'enable_upi': True,
            'enable_razorpay': True,
            'updated_at': datetime.utcnow()
        }
        db.payment_settings.insert_one(default_settings)
        settings = db.payment_settings.find_one({})
    return serialize(settings)

def update_payment_settings(data: dict) -> dict:
    db = get_db()
    allowed = {}
    for key in ['upi_id', 'payee_name', 'merchant_name', 'razorpay_key_id', 'enable_upi', 'enable_razorpay']:
        if key in data:
            allowed[key] = data[key]
    allowed['updated_at'] = datetime.utcnow()

    db.payment_settings.update_one({}, {'$set': allowed}, upsert=True)
    return get_payment_settings()

