from database.db import get_db
from bson import ObjectId
from datetime import datetime

def serialize(doc):
    if not doc:
        return None
    doc = dict(doc)
    doc['_id'] = str(doc['_id'])
    return doc

def create_note(data: dict) -> dict:
    db = get_db()
    doc = {
        'standard': int(data['standard']),
        'subject': data.get('subject', 'General').strip(),
        'title': data['title'].strip(),
        'description': data.get('description', '').strip(),
        'file_link': data.get('file_link', '').strip(),
        'teacher_name': data.get('teacher_name', 'Class Teacher'),
        'created_at': datetime.utcnow()
    }
    res = db.notes.insert_one(doc)
    doc['_id'] = str(res.inserted_id)
    return doc

def get_notes_by_standard(standard: int) -> list:
    db = get_db()
    notes = list(db.notes.find({'standard': int(standard)}).sort('created_at', -1))
    return [serialize(n) for n in notes]

def delete_note(note_id: str) -> bool:
    db = get_db()
    try:
        res = db.notes.delete_one({'_id': ObjectId(note_id)})
        return res.deleted_count > 0
    except Exception:
        return False
