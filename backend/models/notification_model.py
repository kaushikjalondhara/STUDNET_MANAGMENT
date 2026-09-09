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

def create_notification(type_name: str, title: str, message: str, standard: int = None, student_id: str = None, link: str = None) -> dict:
    """
    Creates a notification.
    If student_id is provided, sent to that specific student.
    If standard is provided without student_id, sent to all students in that standard.
    type_name: 'homework' | 'notice' | 'result' | 'fee' | 'attendance' | 'leave' | 'general'
    """
    # Check if notification type is enabled in School Settings
    try:
        from models.settings_model import is_notification_enabled
        if not is_notification_enabled(type_name):
            return {'status': 'suppressed', 'reason': f'Notifications for {type_name} are disabled in School Settings.'}
    except Exception:
        pass

    db = get_db()
    doc = {
        'type': type_name,
        'title': title,
        'message': message,
        'standard': int(standard) if standard is not None else None,
        'student_id': ObjectId(student_id) if student_id else None,
        'link': link or '',
        'read': False,
        'created_at': datetime.utcnow()
    }
    res = db.notifications.insert_one(doc)
    return serialize(db.notifications.find_one({'_id': res.inserted_id}))

def get_student_notifications(student_id: str, standard: int, limit: int = 50) -> list:
    db = get_db()
    sid = ObjectId(student_id)
    # Match notifications sent specifically to this student OR broadcast to their standard
    query = {
        '$or': [
            {'student_id': sid},
            {'standard': int(standard), 'student_id': None},
            {'standard': None, 'student_id': None}
        ]
    }
    cursor = db.notifications.find(query).sort('created_at', -1).limit(limit)
    return [serialize(doc) for doc in cursor]

def mark_notification_read(notification_id: str) -> bool:
    db = get_db()
    res = db.notifications.update_one({'_id': ObjectId(notification_id)}, {'$set': {'read': True}})
    return res.modified_count > 0

def mark_all_notifications_read(student_id: str, standard: int) -> int:
    db = get_db()
    sid = ObjectId(student_id)
    query = {
        '$or': [
            {'student_id': sid},
            {'standard': int(standard), 'student_id': None}
        ],
        'read': False
    }
    res = db.notifications.update_many(query, {'$set': {'read': True}})
    return res.modified_count

def get_unread_count(student_id: str, standard: int) -> int:
    db = get_db()
    sid = ObjectId(student_id)
    query = {
        '$or': [
            {'student_id': sid},
            {'standard': int(standard), 'student_id': None}
        ],
        'read': False
    }
    return db.notifications.count_documents(query)
