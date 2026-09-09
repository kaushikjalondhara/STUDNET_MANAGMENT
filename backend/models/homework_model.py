from database.db import get_db
from bson import ObjectId
from datetime import datetime

def serialize(doc) -> dict:
    if doc is None:
        return None
    doc = dict(doc)
    if '_id' in doc:
        doc['_id'] = str(doc['_id'])
    return doc

def get_homework_by_standard(standard: int) -> list:
    db = get_db()
    records = list(db.homework.find({'standard': int(standard)}).sort('due_date', 1))
    return [serialize(r) for r in records]

def create_homework(data: dict) -> dict:
    db = get_db()
    doc = {
        'standard': int(data['standard']),
        'subject': data.get('subject', 'General').strip(),
        'title': data.get('title', '').strip(),
        'description': data.get('description', '').strip(),
        'due_date': data.get('due_date', ''),
        'created_at': datetime.utcnow()
    }
    res = db.homework.insert_one(doc)
    doc['_id'] = str(res.inserted_id)
    return doc

def delete_homework(hw_id: str) -> bool:
    db = get_db()
    res = db.homework.delete_one({'_id': ObjectId(hw_id)})
    return res.deleted_count > 0
