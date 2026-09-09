from database.db import get_db
from bson import ObjectId
from datetime import datetime

DEFAULT_SUBJECTS = [
    'Mathematics',
    'Science',
    'English',
    'Social Science',
    'Gujarati',
    'Hindi'
]

GRADE_THRESHOLDS = [
    (90, 'A+'), (80, 'A'), (70, 'B+'), (60, 'B'),
    (50, 'C'), (40, 'D'), (0, 'F')
]

def serialize(doc) -> dict:
    if doc is None:
        return None
    doc = dict(doc)
    if '_id' in doc:
        doc['_id'] = str(doc['_id'])
    if 'student_id' in doc and isinstance(doc['student_id'], ObjectId):
        doc['student_id'] = str(doc['student_id'])
    return doc

def calculate_grade(pct: float) -> str:
    for threshold, grade in GRADE_THRESHOLDS:
        if pct >= threshold:
            return grade
    return 'F'

def calculate_status(subjects: list, pct: float) -> str:
    if pct < 40:
        return 'Fail'
    for s in subjects:
        marks = float(s.get('marks', 0))
        max_m = float(s.get('max_marks', 100))
        # Subject pass mark is 35%
        if max_m > 0 and (marks / max_m * 100) < 35:
            return 'Fail'
    return 'Pass'

def get_results_by_standard(standard: int) -> list:
    """Return all comprehensive exam report cards for a standard."""
    db = get_db()
    pipeline = [
        {'$match': {'standard': standard}},
        {'$lookup': {
            'from': 'students',
            'localField': 'student_id',
            'foreignField': '_id',
            'as': 'student'
        }},
        {'$unwind': {'path': '$student', 'preserveNullAndEmptyArrays': True}},
        {'$sort': {'student.roll_no': 1, 'created_at': -1}}
    ]
    results = []
    for r in db.results.aggregate(pipeline):
        s = r.get('student', {})
        subjects = r.get('subjects', [])
        
        # Backwards compatibility if old single-subject schema exists
        if not subjects and 'subject' in r:
            subjects = [{
                'subject': r.get('subject', 'Subject'),
                'marks': r.get('marks', 0),
                'max_marks': r.get('max_marks', 100)
            }]
            
        total_marks = float(r.get('total_marks', sum(float(sub.get('marks', 0)) for sub in subjects)))
        max_total = float(r.get('max_total', sum(float(sub.get('max_marks', 100)) for sub in subjects)))
        pct = round(total_marks / max_total * 100, 1) if max_total > 0 else 0
        grade = r.get('grade') or calculate_grade(pct)
        status = r.get('status') or calculate_status(subjects, pct)

        results.append({
            '_id': str(r['_id']),
            'student_id': str(r.get('student_id', '')),
            'student_name': s.get('name', 'Unknown'),
            'roll_no': s.get('roll_no', '—'),
            'standard': r.get('standard'),
            'exam_name': r.get('exam_name', 'Exam'),
            'subjects': subjects,
            'total_marks': round(total_marks, 1),
            'max_total': round(max_total, 1),
            'percentage': pct,
            'grade': grade,
            'status': status,
            'created_at': r.get('created_at', '').isoformat() if hasattr(r.get('created_at', ''), 'isoformat') else ''
        })
    return results

def create_result(data: dict) -> dict:
    db = get_db()
    student_id = ObjectId(data['student_id'])
    standard = int(data['standard'])
    exam_name = data.get('exam_name', 'Final Exam').strip()
    raw_subjects = data.get('subjects', [])

    subjects = []
    total_marks = 0.0
    max_total = 0.0

    for sub in raw_subjects:
        sub_name = sub.get('subject', '').strip()
        if not sub_name:
            continue
        marks = float(sub.get('marks', 0))
        max_m = float(sub.get('max_marks', 100))
        subjects.append({
            'subject': sub_name,
            'marks': marks,
            'max_marks': max_m
        })
        total_marks += marks
        max_total += max_m

    pct = round(total_marks / max_total * 100, 1) if max_total > 0 else 0
    grade = calculate_grade(pct)
    status = calculate_status(subjects, pct)

    doc = {
        'student_id': student_id,
        'standard': standard,
        'exam_name': exam_name,
        'subjects': subjects,
        'total_marks': round(total_marks, 1),
        'max_total': round(max_total, 1),
        'percentage': pct,
        'grade': grade,
        'status': status,
        'created_at': datetime.utcnow()
    }

    # Upsert per student + exam_name
    db.results.update_one(
        {'student_id': student_id, 'exam_name': exam_name},
        {'$set': doc},
        upsert=True
    )
    saved = db.results.find_one({'student_id': student_id, 'exam_name': exam_name})
    return serialize(saved)

def update_result(result_id: str, data: dict) -> dict | None:
    db = get_db()
    existing = db.results.find_one({'_id': ObjectId(result_id)})
    if not existing:
        return None

    raw_subjects = data.get('subjects', existing.get('subjects', []))
    exam_name = data.get('exam_name', existing.get('exam_name', 'Final Exam')).strip()

    subjects = []
    total_marks = 0.0
    max_total = 0.0

    for sub in raw_subjects:
        sub_name = sub.get('subject', '').strip()
        if not sub_name:
            continue
        marks = float(sub.get('marks', 0))
        max_m = float(sub.get('max_marks', 100))
        subjects.append({
            'subject': sub_name,
            'marks': marks,
            'max_marks': max_m
        })
        total_marks += marks
        max_total += max_m

    pct = round(total_marks / max_total * 100, 1) if max_total > 0 else 0
    grade = calculate_grade(pct)
    status = calculate_status(subjects, pct)

    update = {
        'exam_name': exam_name,
        'subjects': subjects,
        'total_marks': round(total_marks, 1),
        'max_total': round(max_total, 1),
        'percentage': pct,
        'grade': grade,
        'status': status,
        'updated_at': datetime.utcnow()
    }

    db.results.update_one({'_id': ObjectId(result_id)}, {'$set': update})
    return serialize(db.results.find_one({'_id': ObjectId(result_id)}))

def delete_result(result_id: str) -> bool:
    db = get_db()
    res = db.results.delete_one({'_id': ObjectId(result_id)})
    return res.deleted_count > 0

def get_student_results(student_id: str) -> dict:
    """Return all exam reports for a specific student."""
    db = get_db()
    sid = ObjectId(student_id)
    records = list(db.results.find({'student_id': sid}).sort('created_at', -1))

    processed = []
    total_pct_sum = 0.0

    for r in records:
        subjects = r.get('subjects', [])
        if not subjects and 'subject' in r:
            subjects = [{
                'subject': r.get('subject', 'Subject'),
                'marks': r.get('marks', 0),
                'max_marks': r.get('max_marks', 100)
            }]
        total_marks = float(r.get('total_marks', sum(float(sub.get('marks', 0)) for sub in subjects)))
        max_total = float(r.get('max_total', sum(float(sub.get('max_marks', 100)) for sub in subjects)))
        pct = round(total_marks / max_total * 100, 1) if max_total > 0 else 0
        total_pct_sum += pct

        processed.append({
            '_id': str(r['_id']),
            'exam_name': r.get('exam_name', 'Exam'),
            'subjects': subjects,
            'total_marks': round(total_marks, 1),
            'max_total': round(max_total, 1),
            'percentage': pct,
            'grade': r.get('grade') or calculate_grade(pct),
            'status': r.get('status') or calculate_status(subjects, pct),
            'created_at': r.get('created_at', '').isoformat() if hasattr(r.get('created_at', ''), 'isoformat') else ''
        })

    avg_score = round(total_pct_sum / len(processed), 1) if processed else 0
    return {
        'results': processed,
        'average_score': avg_score,
        'overall_grade': calculate_grade(avg_score) if processed else '—'
    }

def get_class_average(standard: int) -> float:
    results = get_results_by_standard(standard)
    if not results:
        return 0.0
    return round(sum(r['percentage'] for r in results) / len(results), 1)

class_average = get_class_average
