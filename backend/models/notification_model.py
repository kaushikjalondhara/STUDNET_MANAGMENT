from database.db import get_db
from bson import ObjectId
from datetime import datetime, timedelta, timezone

# Indian Standard Time = UTC + 5:30
IST = timezone(timedelta(hours=5, minutes=30))

def serialize(doc) -> dict:
    if doc is None:
        return None
    doc = dict(doc)
    if '_id' in doc:
        doc['_id'] = str(doc['_id'])
    if 'student_id' in doc and isinstance(doc['student_id'], ObjectId):
        doc['student_id'] = str(doc['student_id'])
    if 'read_by' in doc and isinstance(doc['read_by'], list):
        doc['read_by'] = [str(x) for x in doc['read_by']]
    if 'created_at' in doc and isinstance(doc['created_at'], datetime):
        # Convert UTC → IST for display
        ist_time = doc['created_at'].replace(tzinfo=timezone.utc).astimezone(IST)
        doc['date_formatted'] = ist_time.strftime("%d-%m-%Y")
        doc['datetime_formatted'] = ist_time.strftime("%d-%m-%Y %I:%M %p")
        doc['created_at'] = ist_time.isoformat()
    return doc

def create_notification(type_name: str, title: str, message: str, standard: int = None, student_id: str = None, link: str = None) -> dict:
    """
    Creates a notification.
    If student_id is provided, sent to that specific student.
    If standard is provided without student_id, sent to all students in that standard.
    If standard is 0, '0', or None without student_id, sent to ALL students across the school.
    type_name: 'homework' | 'notice' | 'result' | 'fee' | 'attendance' | 'leave' | 'notes' | 'general'
    """
    # Check if notification type is enabled in School Settings
    try:
        from models.settings_model import is_notification_enabled
        if not is_notification_enabled(type_name):
            print(f"  ⚠️ Notification SUPPRESSED: type={type_name}, title={title} (disabled in School Settings)")
            return {'status': 'suppressed', 'reason': f'Notifications for {type_name} are disabled in School Settings.'}
    except Exception as e:
        print(f"  ⚠️ Notification settings check failed: {e} (allowing notification)")

    valid_sid = None
    if student_id:
        try:
            valid_sid = ObjectId(student_id)
        except Exception:
            valid_sid = str(student_id)

    std_val = None
    if standard is not None:
        try:
            std_val = int(standard)
        except Exception:
            std_val = None

    db = get_db()
    doc = {
        'type': type_name,
        'title': title,
        'message': message,
        'standard': std_val,
        'student_id': valid_sid,
        'link': link or '',
        'read': False,
        'read_by': [],
        'created_at': datetime.utcnow()
    }
    res = db.notifications.insert_one(doc)
    print(f"  🔔 Notification CREATED: type={type_name}, std={std_val}, sid={valid_sid}, title={title[:50]}")
    return serialize(db.notifications.find_one({'_id': res.inserted_id}))

def _build_student_query(student_id: str, standard: int) -> dict:
    try:
        sid = ObjectId(student_id)
    except Exception:
        sid = str(student_id)

    try:
        std_num = int(standard)
    except Exception:
        std_num = 1

    str_sid = str(student_id)

    # Condition for broadcast notifications (student_id is null/missing/empty)
    broadcast_sid_check = {'$or': [
        {'student_id': None},
        {'student_id': {'$exists': False}},
        {'student_id': ''},
        {'student_id': False}
    ]}

    # Standard matching: match student's standard, or global (0/null/missing)
    std_match = {'$or': [
        {'standard': std_num},
        {'standard': str(std_num)},
        {'standard': 0},
        {'standard': '0'},
        {'standard': None},
        {'standard': {'$exists': False}}
    ]}

    return {
        '$or': [
            # Personal notifications for this student (by ObjectId or string)
            {'student_id': sid},
            {'student_id': str_sid},
            # Broadcast notifications for this student's standard or all standards
            {'$and': [broadcast_sid_check, std_match]}
        ]
    }

def get_student_notifications(student_id: str, standard: int, limit: int = 50) -> list:
    db = get_db()
    query = _build_student_query(student_id, standard)
    cursor = db.notifications.find(query).sort('created_at', -1).limit(limit)
    str_sid = str(student_id)
    results = []
    for doc in cursor:
        serialized = serialize(doc)
        read_by = doc.get('read_by') or []
        is_read = False
        if str_sid in [str(x) for x in read_by]:
            is_read = True
        elif doc.get('student_id') and doc.get('read') is True:
            is_read = True
        serialized['read'] = is_read
        results.append(serialized)
    return results

def mark_notification_read(notification_id: str, student_id: str = None) -> bool:
    db = get_db()
    try:
        oid = ObjectId(notification_id)
    except Exception:
        return False

    doc = db.notifications.find_one({'_id': oid})
    if not doc:
        return False

    str_sid = str(student_id) if student_id else None

    # If it's a broadcast notification (student_id is None) and student_id is provided
    if not doc.get('student_id') and str_sid:
        db.notifications.update_one(
            {'_id': oid},
            {'$addToSet': {'read_by': str_sid}}
        )
    else:
        # Personal notification or general mark
        update = {'$set': {'read': True}}
        if str_sid:
            update['$addToSet'] = {'read_by': str_sid}
        db.notifications.update_one({'_id': oid}, update)

    return True

def mark_all_notifications_read(student_id: str, standard: int) -> int:
    db = get_db()
    query = _build_student_query(student_id, standard)
    str_sid = str(student_id)
    try:
        sid = ObjectId(student_id)
    except Exception:
        sid = str_sid

    # 1. Add student_id to read_by for all matching broadcast & personal notifications
    res = db.notifications.update_many(query, {'$addToSet': {'read_by': str_sid}})

    # 2. Also set read: True for personal notifications of this student
    db.notifications.update_many(
        {'$or': [{'student_id': sid}, {'student_id': str_sid}]},
        {'$set': {'read': True}}
    )
    return res.modified_count

def get_unread_count(student_id: str, standard: int) -> int:
    db = get_db()
    str_sid = str(student_id)

    # Reuse the same query builder for consistency
    base_query = _build_student_query(student_id, standard)

    # Broadcast notification check: student_id is null/missing/empty
    broadcast_sid_check = {'$or': [
        {'student_id': None},
        {'student_id': {'$exists': False}},
        {'student_id': ''},
        {'student_id': False}
    ]}

    query = {
        '$and': [
            base_query,
            {
                'read_by': {'$ne': str_sid}
            },
            {
                '$or': [
                    broadcast_sid_check,
                    {'read': {'$ne': True}}
                ]
            }
        ]
    }
    return db.notifications.count_documents(query)

def sync_missing_notice_notifications():
    """Ensure any notices in db.notices have a corresponding notification in db.notifications."""
    db = get_db()
    try:
        notices = list(db.notices.find())
        for n in notices:
            title = f'📢 Notice: {n.get("title", "").strip()}'
            existing = db.notifications.find_one({'type': 'notice', 'title': title})
            if not existing:
                c_at = n.get('created_at') or datetime.utcnow()
                today_str = c_at.strftime("%d-%m-%Y") if isinstance(c_at, datetime) else ''
                msg = n.get('description') or n.get('title') or ''
                doc = {
                    'type': 'notice',
                    'title': title,
                    'message': f'📅 તારીખ / Date: {today_str} — {msg[:120]}',
                    'standard': n.get('standard', 0),
                    'student_id': None,
                    'link': 'notices.html',
                    'read': False,
                    'read_by': [],
                    'created_at': c_at
                }
                db.notifications.insert_one(doc)
    except Exception as e:
        print("sync_missing_notice_notifications error:", e)
