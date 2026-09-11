import os
import bcrypt as _bcrypt
import secrets
from datetime import datetime, timedelta
from database.db import get_db

DEFAULT_MANAGEMENT_PASSWORD = os.environ.get('DEFAULT_MANAGEMENT_PASSWORD', 'admin123')

def _hash_password(plain: str) -> str:
    return _bcrypt.hashpw(plain.strip().encode('utf-8'), _bcrypt.gensalt()).decode('utf-8')

def _check_password(plain: str, hashed: str) -> bool:
    try:
        return _bcrypt.checkpw(plain.strip().encode('utf-8'), hashed.encode('utf-8'))
    except Exception:
        return False

# ─── Management Auth ──────────────────────────────────────────────────────────

def init_management_auth():
    """Ensure management password record exists in DB."""
    db = get_db()
    auth_doc = db.management_auth.find_one({})
    if not auth_doc:
        doc = {
            'password_hash': _hash_password(DEFAULT_MANAGEMENT_PASSWORD),
            'failed_attempts': 0,
            'lockout_until': None,
            'active_tokens': [],
            'updated_at': datetime.utcnow()
        }
        db.management_auth.insert_one(doc)
        print("  → Management password initialized: default admin123")

def verify_management_password(password: str) -> tuple[bool, str]:
    """
    Verifies management password.
    Returns (True, session_token) on success.
    Returns (False, error_message) on failure.
    """
    db = get_db()
    init_management_auth()
    doc = db.management_auth.find_one({}, sort=[('updated_at', -1)])
    if not doc:
        return False, 'Management account not found.'

    now = datetime.utcnow()

    # Check lockout
    lockout_until = doc.get('lockout_until')
    if lockout_until and now < lockout_until:
        rem_mins = max(1, int((lockout_until - now).total_seconds() / 60))
        return False, f'Account locked due to too many failed attempts. Please try again after {rem_mins} minute(s).'

    pw_hash = doc.get('password_hash', '')
    if _check_password(password, pw_hash):
        # Successful login: reset failed attempts, generate session token
        token = secrets.token_urlsafe(32)
        token_entry = {
            'token': token,
            'created_at': now,
            'expires_at': now + timedelta(hours=4)
        }
        valid_tokens = [
            t for t in doc.get('active_tokens', [])
            if t.get('expires_at') and t['expires_at'] > now
        ]
        valid_tokens.append(token_entry)

        db.management_auth.update_one(
            {'_id': doc['_id']},
            {
                '$set': {
                    'failed_attempts': 0,
                    'lockout_until': None,
                    'active_tokens': valid_tokens,
                    'last_login': now
                }
            }
        )
        return True, token
    else:
        # Failed attempt
        failed = doc.get('failed_attempts', 0) + 1
        lockout = None
        if failed >= 5:
            lockout = now + timedelta(minutes=15)
            db.management_auth.update_one(
                {'_id': doc['_id']},
                {
                    '$set': {
                        'failed_attempts': failed,
                        'lockout_until': lockout
                    }
                }
            )
            return False, 'Account locked due to too many failed attempts. Please try again after 15 minutes.'

        db.management_auth.update_one(
            {'_id': doc['_id']},
            {'$set': {'failed_attempts': failed}}
        )
        remaining = 5 - failed
        return False, f'Incorrect Management Password. ({remaining} attempt(s) remaining before temporary lockout)'

def is_valid_management_token(token: str) -> bool:
    """Validate management session token."""
    if not token:
        return False
    db = get_db()
    # Sort by updated_at DESC to always get the most recently updated auth document
    doc = db.management_auth.find_one({}, sort=[('updated_at', -1)])
    if not doc:
        return False
    now = datetime.utcnow()
    for t in doc.get('active_tokens', []):
        if t.get('token') == token and t.get('expires_at') and t['expires_at'] > now:
            return True
    return False

def change_management_password(old_password: str, new_password: str) -> tuple[bool, str]:
    """Change management password after validating old password."""
    if not new_password or len(new_password.strip()) < 4:
        return False, 'New password must be at least 4 characters long.'

    db = get_db()
    init_management_auth()
    doc = db.management_auth.find_one({}, sort=[('updated_at', -1)])
    if not doc:
        return False, 'Management record not found.'

    if not _check_password(old_password, doc.get('password_hash', '')):
        return False, 'Incorrect current management password.'

    new_hash = _hash_password(new_password)
    db.management_auth.update_one(
        {'_id': doc['_id']},
        {
            '$set': {
                'password_hash': new_hash,
                'failed_attempts': 0,
                'lockout_until': None,
                'active_tokens': [],
                'updated_at': datetime.utcnow()
            }
        }
    )
    return True, 'Management password updated successfully. Please login again.'

def get_default_hall_ticket_schedule(standard: int = 1) -> list:
    std = int(standard)
    room = f"Room 10{((std - 1) % 4) + 1}"
    return [
        {'date': '2026-10-15', 'day': 'Thursday',  'subject': 'Mathematics',      'time': '09:00 AM - 12:00 PM', 'room': room},
        {'date': '2026-10-17', 'day': 'Saturday',  'subject': 'Science & Tech',   'time': '09:00 AM - 12:00 PM', 'room': room},
        {'date': '2026-10-19', 'day': 'Monday',    'subject': 'English Language', 'time': '09:00 AM - 12:00 PM', 'room': room},
        {'date': '2026-10-21', 'day': 'Wednesday', 'subject': 'Social Science',   'time': '09:00 AM - 12:00 PM', 'room': room},
        {'date': '2026-10-23', 'day': 'Friday',    'subject': 'Gujarati / Hindi', 'time': '09:00 AM - 12:00 PM', 'room': room},
        {'date': '2026-10-26', 'day': 'Monday',    'subject': 'Computer & AI',    'time': '09:00 AM - 11:30 AM', 'room': 'Computer Lab 1'},
    ]

def get_default_hall_ticket_config(standard: int = 1) -> dict:
    std = int(standard)
    title = 'Annual Board Examination 2026-27' if std in [10, 12] else f'Standard {std} Annual Examination 2026-27'
    return {
        'enabled': True,
        'exam_title': title,
        'instructions': (
            "1. Candidates must carry this Hall Ticket and School ID Card into the examination hall daily.\n"
            "2. Reach the examination room at least 15 minutes before the scheduled commencement time.\n"
            "3. Electronic devices, smartphones, smartwatches, and study notes are strictly forbidden.\n"
            "4. Maintain pin-drop silence; unfair means will result in immediate disqualification."
        ),
        'schedule': get_default_hall_ticket_schedule(std)
    }

# ─── Default School Settings ─────────────────────────────────────────────────

DEFAULT_SCHOOL_SETTINGS = {
    'school_info': {
        'name': 'Parth classic',
        'logo': '/css/school-logo.png',
        'address': '123 Education Boulevard, Knowledge City, Gujarat 380001',
        'mobile': '+91 98765 43210',
        'email': 'info@parthclassic.edu.in',
        'website': 'https://edumanagepro.edu',
        'academic_year': '2026-2027'
    },
    'academic': {
        'academic_year': '2026-2027',
        'standards': [
            {'standard': i, 'label': f'Standard {i}', 'active': True, 'divisions': ['A', 'B']}
            for i in range(1, 13)
        ],
        'divisions': ['A', 'B', 'C'],
        'subjects': ['Mathematics', 'Science', 'English', 'Social Science', 'Gujarati', 'Hindi', 'Computer Science'],
        'exam_types': ['Unit Test 1', 'Unit Test 2', 'Mid Term Exam', 'Final Exam', 'Practical']
    },
    'fees': {
        'standard_fees': {
            '1': 15000,
            '2': 16000,
            '3': 17000,
            '4': 18000,
            '5': 20000,
            '6': 22000,
            '7': 24000,
            '8': 26000,
            '9': 28000,
            '10': 30000,
            '11': 35000,
            '12': 40000
        },
        'fee_types': [
            {'name': 'Tuition Fees', 'percentage': 60},
            {'name': 'Exam Fees', 'percentage': 10},
            {'name': 'Computer Fees', 'percentage': 15},
            {'name': 'Other Fees', 'percentage': 15}
        ],
        'due_date': '2026-10-31',
        'installments': 'Quarterly (4 Installments) or One-time',
        'late_fee': 200,
        'discount': '5% sibling concession, 10% full annual prepayment discount',
        'upi_id': 'schoolfees@oksbi',
        'payee_name': 'EduManage Pro Public School',
        'merchant_name': 'EduManage Pro School',
        'merchant_code': '8211',
        'razorpay_key_id': 'rzp_test_1DP5mmOlF5G5ag',
        'enable_upi': True,
        'enable_razorpay': True
    },
    'attendance': {
        'present_code': 'P',
        'absent_code': 'A',
        'late_code': 'L',
        'half_day_code': 'H',
        'late_rule': '3 late arrivals equal 1 absence',
        'min_attendance_pct': 75
    },
    'exam': {
        'exam_types': ['Unit Test 1', 'Unit Test 2', 'Mid Term Exam', 'Final Exam', 'Practical'],
        'max_marks': 100,
        'passing_marks': 35,
        'grade_system': [
            {'grade': 'A+', 'min_pct': 90, 'remark': 'Outstanding'},
            {'grade': 'A',  'min_pct': 80, 'remark': 'Excellent'},
            {'grade': 'B+', 'min_pct': 70, 'remark': 'Very Good'},
            {'grade': 'B',  'min_pct': 60, 'remark': 'Good'},
            {'grade': 'C',  'min_pct': 50, 'remark': 'Satisfactory'},
            {'grade': 'D',  'min_pct': 35, 'remark': 'Pass'},
            {'grade': 'F',  'min_pct': 0,  'remark': 'Needs Improvement'}
        ],
        'percentage_rule': 'Standard Rounding to 1 Decimal'
    },
    'timetable': {
        'start_time': '08:00',
        'end_time': '14:00',
        'period_duration_mins': 45,
        'lunch_break_start': '11:30',
        'lunch_break_end': '12:00',
        'periods_per_day': 7
    },
    'homework': {
        'categories': ['Daily Class Homework', 'Weekly Assignment', 'Science / Math Project', 'Holiday Assignment'],
        'submission_rules': 'Must be submitted on or before due date morning 09:00 AM.',
        'default_due_days': 1
    },
    'notifications': {
        'attendance': True,
        'homework': True,
        'notes': True,
        'notice': True,
        'result': True,
        'leave': True,
        'fee_reminder': True,
        'payment': True,
        'receipt': True
    },
    'notices': {
        'categories': ['General Notice', 'Academic Schedule', 'Sports & Activities', 'Cultural Events', 'Holiday Notice', 'Emergency Alert'],
        'priorities': ['Low', 'Normal', 'High', 'Urgent'],
        'default_expiry_days': 15,
        'target_standard': 'All Standards (1 to 12)',
        'target_division': 'All Divisions'
    },
    'general': {
        'date_format': 'DD/MM/YYYY',
        'time_format': '12-Hour (AM/PM)',
        'currency': '₹',
        'receipt_prefix': 'REC-2026-',
        'working_days': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    },
    'hall_ticket': {
        'standards': {
            str(i): get_default_hall_ticket_config(i)
            for i in range(1, 13)
        }
    }
}

def get_school_settings() -> dict:
    """Retrieve all school settings, seeding defaults if not present."""
    db = get_db()
    doc = db.school_settings.find_one({})
    if not doc:
        doc = dict(DEFAULT_SCHOOL_SETTINGS)
        doc['created_at'] = datetime.utcnow()
        doc['updated_at'] = datetime.utcnow()
        res = db.school_settings.insert_one(doc)
        doc['_id'] = str(res.inserted_id)
        return doc

    doc = dict(doc)
    doc['_id'] = str(doc['_id'])

    updated = False
    for section, defaults in DEFAULT_SCHOOL_SETTINGS.items():
        if section not in doc:
            doc[section] = defaults
            updated = True
        elif isinstance(defaults, dict):
            for k, v in defaults.items():
                if k not in doc[section]:
                    doc[section][k] = v
                    updated = True

    if updated:
        clean_doc = {k: v for k, v in doc.items() if k != '_id'}
        db.school_settings.update_one({}, {'$set': clean_doc})

    return doc

def update_school_settings(category: str, data: dict) -> dict:
    """Update a specific category or entire school settings."""
    db = get_db()
    current = get_school_settings()

    if category == 'all':
        for cat, val in data.items():
            if cat in DEFAULT_SCHOOL_SETTINGS and isinstance(val, dict):
                current[cat].update(val)
    elif category in DEFAULT_SCHOOL_SETTINGS:
        current[category].update(data)
    else:
        raise ValueError(f"Unknown settings category: {category}")

    current['updated_at'] = datetime.utcnow()
    clean_data = {k: v for k, v in current.items() if k != '_id'}
    db.school_settings.update_one({}, {'$set': clean_data}, upsert=True)

    # Sync payment settings if fees or school_info updated
    if category in ('fees', 'all'):
        fee_data = data if category == 'fees' else data.get('fees', {})
        payment_fields = {}
        for k in ['upi_id', 'payee_name', 'merchant_name', 'merchant_code', 'razorpay_key_id', 'enable_upi', 'enable_razorpay']:
            if k in fee_data:
                payment_fields[k] = fee_data[k]
        if payment_fields:
            payment_fields['updated_at'] = datetime.utcnow()
            db.payment_settings.update_one({}, {'$set': payment_fields}, upsert=True)

        # Sync fee due_date to all student fee records
        if 'due_date' in fee_data and fee_data['due_date']:
            db.fees.update_many({}, {'$set': {'due_date': fee_data['due_date'], 'updated_at': datetime.utcnow()}})

        # Sync standard fee rates to all student fee records
        if 'standard_fees' in fee_data and isinstance(fee_data['standard_fees'], dict):
            from pymongo import UpdateOne
            bulk_ops = []
            
            for std_str, fee_val in fee_data['standard_fees'].items():
                try:
                    std_num = int(std_str)
                    new_tot = float(fee_val)
                    cfg = get_standard_fee_config(std_num)
                    
                    # Get all students for this standard
                    std_students = list(db.students.find({'standard': std_num}))
                    student_ids = [s['_id'] for s in std_students]
                    
                    if student_ids:
                        # Calculate effective total fee with late fee if applicable
                        current_due_date = cfg.get('due_date', '2026-10-31')
                        try:
                            due_date_obj = datetime.strptime(current_due_date, '%Y-%m-%d').date()
                        except:
                            due_date_obj = datetime(2026, 10, 31).date()
                            
                        today = datetime.utcnow().date()
                        is_late = today > due_date_obj
                        late_fee_amt = float(cfg.get('late_fee', 0)) if is_late else 0.0
                        
                        effective_total_fee = new_tot + late_fee_amt
                        base_breakdown = list(cfg.get('breakdown', []))
                        if is_late and late_fee_amt > 0:
                            base_breakdown.append({
                                'head': 'Late Fee',
                                'amount': late_fee_amt
                            })

                        # Fetch all fee records for these students in ONE query (N+1 query fix)
                        fees_records = list(db.fees.find({'student_id': {'$in': student_ids}}))
                        
                        for s_record in fees_records:
                            paid = float(s_record.get('paid_amount', 0))
                            new_pnd = max(0.0, effective_total_fee - paid)
                            new_st = 'Paid' if new_pnd <= 0 else ('Partial' if paid > 0 else 'Unpaid')
                            
                            bulk_ops.append(
                                UpdateOne(
                                    {'_id': s_record['_id']},
                                    {
                                        '$set': {
                                            'total_fee': effective_total_fee,
                                            'pending_amount': new_pnd,
                                            'status': new_st,
                                            'breakdown': base_breakdown,
                                            'updated_at': datetime.utcnow()
                                        }
                                    }
                                )
                            )
                except Exception as e:
                    print(f"Error syncing standard {std_str} fee:", e)
                    
            if bulk_ops:
                try:
                    db.fees.bulk_write(bulk_ops, ordered=False)
                except Exception as e:
                    print("Error during bulk write of fees:", e)

    if category in ('school_info', 'all'):
        info_data = data if category == 'school_info' else data.get('school_info', {})
        if 'name' in info_data and info_data['name']:
            db.payment_settings.update_one({}, {'$set': {'payee_name': info_data['name'], 'merchant_name': info_data['name']}}, upsert=True)
            db.school_settings.update_one({}, {'$set': {'fees.payee_name': info_data['name'], 'fees.merchant_name': info_data['name']}})

    return get_school_settings()

def get_standard_fee_config(standard: int) -> dict:
    """Get configured fee structure for a standard."""
    settings = get_school_settings()
    fee_cfg = settings.get('fees', DEFAULT_SCHOOL_SETTINGS['fees'])
    std_str = str(int(standard))

    std_fees = fee_cfg.get('standard_fees', {})
    total = std_fees.get(std_str)
    if total is None:
        base = 15000 + (int(standard) - 1) * 2000
        total = base

    total = float(total)

    fee_types = fee_cfg.get('fee_types', DEFAULT_SCHOOL_SETTINGS['fees']['fee_types'])
    breakdown = []
    allocated = 0
    for idx, ft in enumerate(fee_types):
        pct = float(ft.get('percentage', 25))
        if idx == len(fee_types) - 1:
            amt = round(total - allocated)
        else:
            amt = round(total * (pct / 100))
            allocated += amt
        breakdown.append({
            'head': ft.get('name', f'Fee Head {idx+1}'),
            'amount': amt
        })

    return {
        'total_fee': total,
        'breakdown': breakdown,
        'due_date': fee_cfg.get('due_date', '2026-10-31'),
        'late_fee': fee_cfg.get('late_fee', 200),
        'discount': fee_cfg.get('discount', ''),
        'installments': fee_cfg.get('installments', 'Quarterly')
    }

def is_notification_enabled(notification_type: str) -> bool:
    """Check whether a notification category is currently enabled in School Settings."""
    try:
        settings = get_school_settings()
        notifs = settings.get('notifications', DEFAULT_SCHOOL_SETTINGS['notifications'])

        mapping = {
            'attendance': 'attendance',
            'homework': 'homework',
            'notes': 'notes',
            'note': 'notes',
            'notice': 'notice',
            'result': 'result',
            'leave': 'leave',
            'fee': 'fee_reminder',
            'fee_reminder': 'fee_reminder',
            'payment': 'payment',
            'receipt': 'receipt',
            'general': 'general'
        }
        key = mapping.get(notification_type.lower(), notification_type.lower())
        # Default to True for unknown/unmapped types (like 'general')
        enabled = bool(notifs.get(key, True))
        if not enabled:
            print(f"  ⚠️ Notification type '{notification_type}' (key='{key}') is DISABLED in School Settings")
        return enabled
    except Exception as e:
        print(f"  ⚠️ is_notification_enabled error: {e} — defaulting to True")
        return True

# ─── Standard-wise Hall Ticket Configuration ─────────────────────────────────

def get_standard_hall_ticket_config(standard: int) -> dict:
    """Get hall ticket settings and schedule for a specific standard."""
    settings = get_school_settings()
    ht_cfg = settings.get('hall_ticket', {})
    std_str = str(int(standard))
    std_data = ht_cfg.get('standards', {}).get(std_str)
    if not std_data:
        std_data = get_default_hall_ticket_config(int(standard))
    return std_data

def update_standard_hall_ticket_config(standard: int, data: dict) -> dict:
    """Save/update hall ticket settings and schedule for a specific standard."""
    db = get_db()
    std_str = str(int(standard))
    settings = get_school_settings()
    ht_cfg = settings.get('hall_ticket', {})
    if 'standards' not in ht_cfg or not isinstance(ht_cfg['standards'], dict):
        ht_cfg['standards'] = {}

    current_std = ht_cfg['standards'].get(std_str) or get_default_hall_ticket_config(int(standard))
    
    exam_title = data.get('exam_title')
    if not exam_title or not str(exam_title).strip():
        exam_title = current_std.get('exam_title', f'Standard {standard} Examination')

    updated_record = {
        'enabled': bool(data.get('enabled', True)),
        'exam_title': str(exam_title).strip(),
        'instructions': str(data.get('instructions', current_std.get('instructions', ''))).strip(),
        'schedule': data.get('schedule', current_std.get('schedule', [])),
        'updated_at': datetime.utcnow()
    }

    db.school_settings.update_one(
        {},
        {
            '$set': {
                f'hall_ticket.standards.{std_str}': updated_record,
                'updated_at': datetime.utcnow()
            }
        },
        upsert=True
    )
    return updated_record

def copy_hall_ticket_config_to_all(source_standard: int) -> dict:
    """Copies the exam title, instructions, and schedule from source_standard to all standards 1-12."""
    db = get_db()
    source_cfg = get_standard_hall_ticket_config(source_standard)
    std_schedule = source_cfg.get('schedule', [])

    updates = {}
    for i in range(1, 13):
        if i == int(source_standard):
            continue
        std_str = str(i)
        room = f"Room 10{((i - 1) % 4) + 1}"
        adj_schedule = []
        for row in std_schedule:
            row_copy = dict(row)
            if 'Room' in row_copy.get('room', ''):
                row_copy['room'] = room
            adj_schedule.append(row_copy)

        title = 'Annual Board Examination 2026-27' if i in [10, 12] else f'Standard {i} Annual Examination 2026-27'
        cfg = {
            'enabled': source_cfg.get('enabled', True),
            'exam_title': source_cfg.get('exam_title') or title,
            'instructions': source_cfg.get('instructions', ''),
            'schedule': adj_schedule,
            'updated_at': datetime.utcnow()
        }
        updates[f'hall_ticket.standards.{std_str}'] = cfg

    updates['updated_at'] = datetime.utcnow()
    db.school_settings.update_one({}, {'$set': updates}, upsert=True)
    return {'success': True, 'message': f'Hall ticket schedule from Standard {source_standard} successfully copied to all standards!'}

