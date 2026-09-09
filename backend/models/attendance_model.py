from database.db import get_db
from bson import ObjectId
from datetime import datetime, date, timedelta
import calendar

def serialize(doc) -> dict:
    if doc is None:
        return None
    doc = dict(doc)
    if '_id' in doc:
        doc['_id'] = str(doc['_id'])
    if 'student_id' in doc and isinstance(doc['student_id'], ObjectId):
        doc['student_id'] = str(doc['student_id'])
    return doc

def get_attendance_for_date(standard: int, date_str: str) -> list:
    """Return attendance records for a standard on a given date."""
    db = get_db()
    records = db.attendance.find({'standard': standard, 'date': date_str})
    return [serialize(r) for r in records]

def get_attendance_summary(standard: int) -> dict:
    """Monthly attendance summary for current month for a standard."""
    db = get_db()
    today = date.today()
    month_prefix = f"{today.year:04d}-{today.month:02d}"
    
    students = list(db.students.find({'standard': int(standard)}, {'_id': 1}))
    student_ids = [s['_id'] for s in students] + [str(s['_id']) for s in students]
    
    pipeline = [
        {'$match': {'standard': int(standard), 'student_id': {'$in': student_ids}, 'date': {'$regex': f'^{month_prefix}'}}},
        {'$group': {
            '_id': '$student_id',
            'total':   {'$sum': 1},
            'present': {'$sum': {'$cond': [{'$eq': ['$status', 'present']}, 1, 0]}}
        }}
    ]
    result = list(db.attendance.aggregate(pipeline))
    if not result:
        return {'total_students': len(students), 'avg_attendance_pct': 0}
    total = len(result)
    avg_pct = sum(
        (r['present'] / r['total'] * 100) if r['total'] > 0 else 0
        for r in result
    ) / total
    return {'total_students': total, 'avg_attendance_pct': round(avg_pct, 1)}

def get_today_stats(standard: int, date_str: str = None) -> dict:
    if not date_str:
        date_str = date.today().isoformat()
    db = get_db()
    # Get all student IDs enrolled in this standard
    students = list(db.students.find({'standard': int(standard)}, {'_id': 1}))
    valid_ids = {str(s['_id']) for s in students}
    
    records = list(db.attendance.find({'standard': int(standard), 'date': date_str}))
    
    # Deduplicate by student_id to prevent any duplicate counts
    seen_status = {}
    for r in records:
        sid_str = str(r.get('student_id') or '')
        if sid_str in valid_ids:
            seen_status[sid_str] = (r.get('status') or '').lower()
            
    present = sum(1 for status in seen_status.values() if status == 'present')
    absent  = sum(1 for status in seen_status.values() if status == 'absent')
    return {'present_today': present, 'absent_today': absent, 'date': date_str}

def upsert_attendance_record(student_id: str, standard: int, date_str: str, status: str) -> dict:
    db = get_db()
    sid = ObjectId(student_id)
    doc = {
        'student_id': sid,
        'standard': standard,
        'date': date_str,
        'status': status.lower(),
        'updated_at': datetime.utcnow()
    }
    db.attendance.update_one(
        {'student_id': sid, 'date': date_str},
        {'$set': doc},
        upsert=True
    )
    return serialize(db.attendance.find_one({'student_id': sid, 'date': date_str}))

def bulk_upsert_attendance(standard: int, date_str: str, records: list) -> int:
    """records = [{student_id, status}, ...]"""
    count = 0
    for r in records:
        upsert_attendance_record(r['student_id'], standard, date_str, r['status'])
        count += 1
    return count

def get_student_attendance(student_id: str) -> dict:
    """
    Monthly attendance calculator:
    Calculates total days in the month (or days elapsed up to today).
    Any day where attendance was not taken or marked absent is counted as ABSENT.
    """
    db = get_db()
    sid = ObjectId(student_id)
    
    # Existing explicit attendance records
    db_records = list(db.attendance.find({'student_id': sid}))
    record_map = {r['date']: (r.get('status') or '').lower() for r in db_records}

    today = date.today()
    current_year = today.year
    current_month = today.month
    
    # Days in current month up to today (e.g. 1st to 9th) or total month days
    _, total_month_days = calendar.monthrange(current_year, current_month)
    days_elapsed = today.day

    # Generate full daily records for the current month up to today
    monthly_history = []
    present_count = 0

    for day in range(days_elapsed, 0, -1):
        day_date = date(current_year, current_month, day)
        date_str = day_date.isoformat()
        
        status = record_map.get(date_str, 'absent')
        if status == 'present':
            present_count += 1
            monthly_history.append({'date': date_str, 'status': 'present'})
        else:
            # Unmarked or absent is counted as absent
            monthly_history.append({'date': date_str, 'status': 'absent'})

    absent_count = days_elapsed - present_count
    pct = round((present_count / days_elapsed * 100), 1) if days_elapsed > 0 else 0

    return {
        'total':          days_elapsed,
        'month_days':     total_month_days,
        'present':        present_count,
        'absent':         absent_count,
        'attendance_pct': pct,
        'history':        monthly_history
    }

def get_attendance_history(standard: int, month: str = None, sort: str = 'asc', limit: int = None, **kwargs) -> list:
    """
    Returns full-month date-wise attendance summary for a standard starting from day 1.
    If attendance was not taken on a day (date <= today), counts all students as absent (present=0, absent=total, pct=0).
    If date > today, marks as upcoming.
    [{date, present, absent, total, attendance_pct, is_marked, status, is_today, is_future}, ...]
    """
    db = get_db()
    today = date.today()
    today_str = today.isoformat()

    if not month:
        year = today.year
        m = today.month
        month = f"{year:04d}-{m:02d}"
    else:
        try:
            parts = month.split('-')
            year = int(parts[0])
            m = int(parts[1])
        except Exception:
            year = today.year
            m = today.month
            month = f"{year:04d}-{m:02d}"

    _, total_month_days = calendar.monthrange(year, m)

    # Total students in this standard
    students = list(db.students.find({'standard': int(standard)}, {'_id': 1}))
    total_students = len(students)

    pipeline = [
        {'$match': {'standard': int(standard), 'date': {'$regex': f'^{month}'}}},
        {'$group': {
            '_id':     '$date',
            'present': {'$sum': {'$cond': [{'$eq': ['$status', 'present']}, 1, 0]}},
            'absent':  {'$sum': {'$cond': [{'$eq': ['$status', 'absent']},  1, 0]}},
            'total':   {'$sum': 1}
        }}
    ]
    db_records = list(db.attendance.aggregate(pipeline))
    db_history = {r['_id']: r for r in db_records}

    history = []
    day_range = range(1, total_month_days + 1)
    if sort == 'desc':
        day_range = range(total_month_days, 0, -1)

    for day in day_range:
        date_str = f"{year:04d}-{m:02d}-{day:02d}"
        is_today = (date_str == today_str)
        is_future = (date_str > today_str)

        if date_str in db_history:
            rec = db_history[date_str]
            tot = rec['total']
            pres = rec['present']
            ab = rec['absent']
            pct = round(pres / tot * 100, 1) if tot > 0 else 0
            history.append({
                'date': date_str,
                'present': pres,
                'absent': ab,
                'total': tot,
                'attendance_pct': pct,
                'is_marked': True,
                'status': 'marked',
                'is_today': is_today,
                'is_future': False
            })
        elif not is_future:
            # Past or today where attendance was NOT taken:
            # "attendence lidhi na hoy to e bdha absent pn hestory akha month ni1 date thi avvioye"
            history.append({
                'date': date_str,
                'present': 0,
                'absent': total_students,
                'total': total_students,
                'attendance_pct': 0,
                'is_marked': False,
                'status': 'all_absent',
                'is_today': is_today,
                'is_future': False
            })
        else:
            # Future date in the month
            history.append({
                'date': date_str,
                'present': 0,
                'absent': 0,
                'total': total_students,
                'attendance_pct': 0,
                'is_marked': False,
                'status': 'upcoming',
                'is_today': False,
                'is_future': True
            })

    if limit and isinstance(limit, int):
        return history[:limit]

    return history

