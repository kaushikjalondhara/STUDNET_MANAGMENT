from database.db import get_db
from bson import ObjectId
from datetime import datetime

def serialize(doc) -> dict:
    if doc is None:
        return None
    doc = dict(doc)
    if '_id' in doc:
        doc['_id'] = str(doc['_id'])
    if 'created_at' in doc and isinstance(doc['created_at'], datetime):
        doc['date_formatted'] = doc['created_at'].strftime("%d-%m-%Y")
        doc['datetime_formatted'] = doc['created_at'].strftime("%d-%m-%Y %I:%M %p")
        doc['created_at'] = doc['created_at'].isoformat()
    return doc

def get_notices(standard: int = None) -> list:
    db = get_db()
    # If standard is specified, match standard OR 0 (all standards)
    query = {}
    if standard is not None:
        query = {'$or': [{'standard': int(standard)}, {'standard': 0}]}
    
    records = list(db.notices.find(query).sort('created_at', -1))
    return [serialize(r) for r in records]

def create_notice(data: dict) -> dict:
    db = get_db()
    standard = int(data.get('standard', 0)) # 0 = All Standards
    doc = {
        'title': data.get('title', '').strip(),
        'description': data.get('description', '').strip(),
        'standard': standard,
        'standard_label': 'All Standards' if standard == 0 else f'Standard {standard}',
        'priority': data.get('priority', 'General'), # Urgent, General, Event
        'posted_by': data.get('posted_by', 'Administration'),
        'created_at': datetime.utcnow()
    }
    res = db.notices.insert_one(doc)
    doc['_id'] = str(res.inserted_id)
    return doc

def delete_notice(notice_id: str) -> bool:
    db = get_db()
    try:
        oid = ObjectId(notice_id)
    except Exception:
        return False
    res = db.notices.delete_one({'_id': oid})
    return res.deleted_count > 0
