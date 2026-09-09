from database.db import get_db
from bson import ObjectId
from datetime import datetime

def serialize(doc) -> dict:
    if doc is None:
        return None
    doc = dict(doc)
    if '_id' in doc:
        doc['_id'] = str(doc['_id'])
    if 'student_id' in doc and isinstance(doc['student_id'], ObjectId):
        doc['student_id'] = str(doc['student_id'])
    return doc

def get_leaves_by_standard(standard: int) -> list:
    db = get_db()
    pipeline = [
        {'$match': {'standard': int(standard)}},
        {'$lookup': {
            'from': 'students',
            'localField': 'student_id',
            'foreignField': '_id',
            'as': 'student'
        }},
        {'$unwind': {'path': '$student', 'preserveNullAndEmptyArrays': True}},
        {'$sort': {'created_at': -1}}
    ]
    results = []
    for r in db.leaves.aggregate(pipeline):
        s = r.get('student', {})
        results.append({
            '_id': str(r['_id']),
            'student_id': str(r.get('student_id', '')),
            'student_name': s.get('name', 'Student'),
            'roll_no': s.get('roll_no', '—'),
            'standard': r.get('standard'),
            'from_date': r.get('from_date', ''),
            'to_date': r.get('to_date', ''),
            'reason': r.get('reason', ''),
            'status': r.get('status', 'Pending'), # Pending, Approved, Rejected
            'admin_remark': r.get('admin_remark', ''),
            'created_at': r.get('created_at', '').isoformat() if hasattr(r.get('created_at', ''), 'isoformat') else ''
        })
    return results

def get_student_leaves(student_id: str) -> list:
    db = get_db()
    records = list(db.leaves.find({'student_id': ObjectId(student_id)}).sort('created_at', -1))
    return [serialize(r) for r in records]

def apply_leave(student_id: str, standard: int, data: dict) -> dict:
    db = get_db()
    doc = {
        'student_id': ObjectId(student_id),
        'standard': int(standard),
        'from_date': data.get('from_date', ''),
        'to_date': data.get('to_date', ''),
        'reason': data.get('reason', '').strip(),
        'status': 'Pending',
        'created_at': datetime.utcnow()
    }
    res = db.leaves.insert_one(doc)
    doc['_id'] = str(res.inserted_id)
    doc['student_id'] = str(doc['student_id'])
    return doc

def update_leave_status(leave_id: str, status: str, remark: str = '') -> dict:
    db = get_db()
    db.leaves.update_one(
        {'_id': ObjectId(leave_id)},
        {'$set': {'status': status, 'admin_remark': remark, 'updated_at': datetime.utcnow()}}
    )
    return serialize(db.leaves.find_one({'_id': ObjectId(leave_id)}))
