from database.db import get_db
from bson import ObjectId
from datetime import datetime
import bcrypt as _bcrypt

def serialize(doc) -> dict:
    if doc is None:
        return None
    doc = dict(doc)
    if '_id' in doc:
        doc['_id'] = str(doc['_id'])
    doc.pop('password_hash', None)
    if not doc.get('password'):
        doc['password'] = '123456' if doc.get('name') == 'abhay' else 'student123'
    return doc

# ─── Queries ────────────────────────────────────────────────────────────────

def get_students_by_standard(standard: int) -> list:
    db = get_db()
    docs = db.students.find({'standard': standard}).sort('roll_no', 1)
    return [serialize(d) for d in docs]

def get_student_by_id(student_id: str) -> dict | None:
    db = get_db()
    doc = db.students.find_one({'_id': ObjectId(student_id)})
    return serialize(doc)

def find_student_by_roll(roll_no: int) -> dict | None:
    """Used for school records / teacher lookup — NOT the login credential."""
    db = get_db()
    return db.students.find_one({'roll_no': roll_no})

def find_student_by_mobile(mobile: str) -> dict | None:
    """Primary login credential lookup."""
    db = get_db()
    return db.students.find_one({'mobile': mobile.strip()})

def create_student(data: dict) -> dict:
    db = get_db()
    pw_str = str(data['password']).strip()
    pw_hash = _bcrypt.hashpw(
        pw_str.encode('utf-8'), _bcrypt.gensalt()
    ).decode('utf-8')
    doc = {
        'name': data['name'].strip(),
        'roll_no': int(data['roll_no']),
        'standard': int(data['standard']),
        'email': (data.get('email') or '').strip().lower() or None,
        'mobile': (data.get('mobile') or '').strip() or None,   # ← mobile (login field)
        'password': pw_str,
        'password_hash': pw_hash,
        'created_at': datetime.utcnow()
    }
    result = db.students.insert_one(doc)
    doc['_id'] = str(result.inserted_id)
    doc.pop('password_hash', None)

    # Automatically initialize standard-wise configured fee structure for new student
    try:
        from models.fee_model import get_or_create_student_fee
        get_or_create_student_fee(str(result.inserted_id), int(data['standard']))
    except Exception as e:
        print("  → Note: fee init deferred:", e)

    return doc

def update_student(student_id: str, data: dict) -> dict | None:
    db = get_db()
    allowed = {k: v for k, v in data.items() if k in ('name', 'email', 'mobile', 'roll_no')}
    if 'roll_no' in allowed:
        allowed['roll_no'] = int(allowed['roll_no'])
    if 'email' in allowed:
        allowed['email'] = (allowed['email'] or '').strip().lower() or None
    if 'mobile' in allowed:
        allowed['mobile'] = (allowed['mobile'] or '').strip() or None
    if 'password' in data and str(data['password']).strip():
        pw_str = str(data['password']).strip()
        allowed['password'] = pw_str
        allowed['password_hash'] = _bcrypt.hashpw(
            pw_str.encode('utf-8'), _bcrypt.gensalt()
        ).decode('utf-8')
    db.students.update_one({'_id': ObjectId(student_id)}, {'$set': allowed})
    return get_student_by_id(student_id)

def delete_student(student_id: str) -> bool:
    db = get_db()
    result = db.students.delete_one({'_id': ObjectId(student_id)})
    return result.deleted_count > 0

def count_by_standard(standard: int) -> int:
    return get_db().students.count_documents({'standard': standard})

# ─── Student auth ────────────────────────────────────────────────────────────

def verify_student_password(student: dict, plain_password: str) -> bool:
    try:
        return _bcrypt.checkpw(
            plain_password.encode('utf-8'),
            student['password_hash'].encode('utf-8')
        )
    except Exception:
        return False
