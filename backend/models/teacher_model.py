from database.db import get_db
from datetime import datetime
import bcrypt as _bcrypt

def serialize(doc) -> dict:
    """Convert MongoDB document to JSON-serializable dict."""
    if doc is None:
        return None
    doc = dict(doc)
    if '_id' in doc:
        doc['_id'] = str(doc['_id'])
    return doc

def find_teacher_by_email(email: str) -> dict | None:
    db = get_db()
    return db.teachers.find_one({'email': email.lower().strip()})

def verify_teacher_password(teacher: dict, plain_password: str) -> bool:
    try:
        return _bcrypt.checkpw(
            plain_password.encode('utf-8'),
            teacher['password_hash'].encode('utf-8')
        )
    except Exception:
        return False

def get_teacher_by_id(teacher_id: str) -> dict | None:
    from bson import ObjectId
    db = get_db()
    doc = db.teachers.find_one({'_id': ObjectId(teacher_id)})
    return serialize(doc)
