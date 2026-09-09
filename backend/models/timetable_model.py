from database.db import get_db
from bson import ObjectId
from datetime import datetime

DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']

DEFAULT_SCHEDULE = {
    'Monday': [
        {'period': 1, 'time': '08:00 - 08:45', 'subject': 'Mathematics', 'room': 'Room 101'},
        {'period': 2, 'time': '08:45 - 09:30', 'subject': 'Science', 'room': 'Lab 1'},
        {'period': 3, 'time': '09:45 - 10:30', 'subject': 'English', 'room': 'Room 101'},
        {'period': 4, 'time': '10:30 - 11:15', 'subject': 'Social Science', 'room': 'Room 101'},
        {'period': 5, 'time': '11:30 - 12:15', 'subject': 'Gujarati', 'room': 'Room 101'},
        {'period': 6, 'time': '12:15 - 01:00', 'subject': 'Hindi', 'room': 'Room 101'}
    ],
    'Tuesday': [
        {'period': 1, 'time': '08:00 - 08:45', 'subject': 'Science', 'room': 'Lab 1'},
        {'period': 2, 'time': '08:45 - 09:30', 'subject': 'Mathematics', 'room': 'Room 101'},
        {'period': 3, 'time': '09:45 - 10:30', 'subject': 'Computer', 'room': 'Comp Lab'},
        {'period': 4, 'time': '10:30 - 11:15', 'subject': 'English', 'room': 'Room 101'},
        {'period': 5, 'time': '11:30 - 12:15', 'subject': 'Social Science', 'room': 'Room 101'},
        {'period': 6, 'time': '12:15 - 01:00', 'subject': 'PT / Sports', 'room': 'Ground'}
    ],
    'Wednesday': [
        {'period': 1, 'time': '08:00 - 08:45', 'subject': 'English', 'room': 'Room 101'},
        {'period': 2, 'time': '08:45 - 09:30', 'subject': 'Gujarati', 'room': 'Room 101'},
        {'period': 3, 'time': '09:45 - 10:30', 'subject': 'Mathematics', 'room': 'Room 101'},
        {'period': 4, 'time': '10:30 - 11:15', 'subject': 'Science', 'room': 'Lab 1'},
        {'period': 5, 'time': '11:30 - 12:15', 'subject': 'Hindi', 'room': 'Room 101'},
        {'period': 6, 'time': '12:15 - 01:00', 'subject': 'Drawing / Art', 'room': 'Art Room'}
    ],
    'Thursday': [
        {'period': 1, 'time': '08:00 - 08:45', 'subject': 'Mathematics', 'room': 'Room 101'},
        {'period': 2, 'time': '08:45 - 09:30', 'subject': 'Social Science', 'room': 'Room 101'},
        {'period': 3, 'time': '09:45 - 10:30', 'subject': 'Science', 'room': 'Lab 1'},
        {'period': 4, 'time': '10:30 - 11:15', 'subject': 'English', 'room': 'Room 101'},
        {'period': 5, 'time': '11:30 - 12:15', 'subject': 'Gujarati', 'room': 'Room 101'},
        {'period': 6, 'time': '12:15 - 01:00', 'subject': 'Library', 'room': 'Library'}
    ],
    'Friday': [
        {'period': 1, 'time': '08:00 - 08:45', 'subject': 'Science', 'room': 'Lab 1'},
        {'period': 2, 'time': '08:45 - 09:30', 'subject': 'Mathematics', 'room': 'Room 101'},
        {'period': 3, 'time': '09:45 - 10:30', 'subject': 'Computer', 'room': 'Comp Lab'},
        {'period': 4, 'time': '10:30 - 11:15', 'subject': 'Hindi', 'room': 'Room 101'},
        {'period': 5, 'time': '11:30 - 12:15', 'subject': 'English', 'room': 'Room 101'},
        {'period': 6, 'time': '12:15 - 01:00', 'subject': 'Music / Dance', 'room': 'Hall'}
    ],
    'Saturday': [
        {'period': 1, 'time': '08:00 - 08:45', 'subject': 'Mathematics', 'room': 'Room 101'},
        {'period': 2, 'time': '08:45 - 09:30', 'subject': 'General Knowledge', 'room': 'Room 101'},
        {'period': 3, 'time': '09:45 - 10:30', 'subject': 'Gujarati', 'room': 'Room 101'},
        {'period': 4, 'time': '10:30 - 11:15', 'subject': 'Yoga / Meditation', 'room': 'Ground'}
    ]
}

def serialize(doc) -> dict:
    if doc is None:
        return None
    doc = dict(doc)
    if '_id' in doc:
        doc['_id'] = str(doc['_id'])
    return doc

def get_timetable(standard: int) -> dict:
    db = get_db()
    record = db.timetables.find_one({'standard': int(standard)})
    if not record:
        # Default generated timetable
        return {
            'standard': int(standard),
            'schedule': DEFAULT_SCHEDULE
        }
    return serialize(record)

def save_timetable(standard: int, schedule: dict) -> dict:
    db = get_db()
    doc = {
        'standard': int(standard),
        'schedule': schedule,
        'updated_at': datetime.utcnow()
    }
    db.timetables.update_one({'standard': int(standard)}, {'$set': doc}, upsert=True)
    return get_timetable(standard)
