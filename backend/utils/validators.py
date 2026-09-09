import re
from datetime import datetime

EMAIL_REGEX = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'

def validate_email(email):
    if not email or not isinstance(email, str):
        return False
    return bool(re.match(EMAIL_REGEX, email.strip()))

def validate_student_data(data, is_update=False):
    if not isinstance(data, dict):
        return False, "Payload must be a JSON object"

    if not is_update:
        required_fields = ['name', 'roll_number', 'email']
        for field in required_fields:
            if not data.get(field) or not str(data.get(field)).strip():
                return False, f"'{field}' is required and cannot be empty"

    if 'email' in data and data['email']:
        if not validate_email(data['email']):
            return False, "Invalid email address format"

    if 'gender' in data and data['gender']:
        valid_genders = ['Male', 'Female', 'Other']
        if data['gender'] not in valid_genders:
            return False, f"Gender must be one of: {', '.join(valid_genders)}"

    if 'dob' in data and data['dob']:
        try:
            datetime.strptime(data['dob'].strip(), '%Y-%m-%d')
        except ValueError:
            return False, "Date of birth must follow YYYY-MM-DD format"

    return True, None

def validate_grade_data(data):
    if not isinstance(data, dict):
        return False, "Payload must be a JSON object"

    for field in ['subject', 'exam_name', 'marks_obtained']:
        if field not in data or str(data[field]).strip() == '':
            return False, f"'{field}' is required"

    try:
        marks = float(data['marks_obtained'])
        max_marks = float(data.get('max_marks', 100.0))
    except (ValueError, TypeError):
        return False, "Marks obtained and Max marks must be numeric"

    if marks < 0:
        return False, "Marks obtained cannot be negative"

    if max_marks <= 0:
        return False, "Max marks must be greater than 0"

    if marks > max_marks:
        return False, "Marks obtained cannot exceed max marks"

    return True, None

def validate_attendance_data(data):
    if not isinstance(data, dict):
        return False, "Payload must be a JSON object"

    for field in ['date', 'status']:
        if not data.get(field) or not str(data.get(field)).strip():
            return False, f"'{field}' is required"

    valid_statuses = ['Present', 'Absent', 'Late']
    if data['status'] not in valid_statuses:
        return False, f"Status must be one of: {', '.join(valid_statuses)}"

    try:
        datetime.strptime(data['date'].strip(), '%Y-%m-%d')
    except ValueError:
        return False, "Date must follow YYYY-MM-DD format"

    return True, None

def validate_login_data(data, identifier_key='email'):
    if not isinstance(data, dict):
        return False, "Payload must be a JSON object"

    if not data.get(identifier_key) or not str(data.get(identifier_key)).strip():
        return False, f"'{identifier_key}' is required"

    if not data.get('password') or not str(data.get('password')).strip():
        return False, "Password is required"

    return True, None
