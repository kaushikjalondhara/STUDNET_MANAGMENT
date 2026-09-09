from pymongo import MongoClient, ASCENDING
from pymongo.errors import DuplicateKeyError
from datetime import datetime
import os
import bcrypt as _bcrypt

_client = None
_db = None

def get_db():
    global _client, _db
    if _db is None:
        mongo_uri = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
        kwargs = {'serverSelectionTimeoutMS': 20000}
        if mongo_uri.startswith('mongodb+srv') or 'ssl=true' in mongo_uri.lower() or 'tls=true' in mongo_uri.lower():
            try:
                import certifi
                kwargs['tlsCAFile'] = certifi.where()
            except Exception:
                pass
        _client = MongoClient(mongo_uri, **kwargs)
        db_name = os.environ.get('DATABASE_NAME', 'student_management')
        _db = _client[db_name]
    return _db

def init_db(app):
    """Initialize indexes and seed demo data."""
    with app.app_context():
        db = get_db()

        # ── Schema migration: phone → mobile ──────────────────────────────────
        # If any student has 'phone' but not 'mobile', drop and re-seed
        old_schema = db.students.count_documents(
            {'phone': {'$exists': True}, 'mobile': {'$exists': False}}
        )
        if old_schema > 0:
            db.students.drop()
            print("  → Schema migration: dropped old students (phone → mobile)")

        # ── Indexes ──────────────────────────────────────────────────────────
        db.teachers.create_index([('email', ASCENDING)], unique=True)
        db.students.create_index([('roll_no', ASCENDING)], unique=True)
        db.students.create_index([('standard', ASCENDING)])
        db.students.create_index([('mobile', ASCENDING)], unique=True, sparse=True)
        db.students.create_index([('email', ASCENDING)], unique=True, sparse=True)
        db.attendance.create_index(
            [('student_id', ASCENDING), ('date', ASCENDING)], unique=True
        )
        db.results.create_index([('student_id', ASCENDING)])

        # ── Seed Data ─────────────────────────────────────────────────────────
        _seed_teachers(db)
        _seed_students(db)
        print("✅ Database initialized and seeded.")

# ── Seeder helpers ───────────────────────────────────────────────────────────

STUDENT_NAMES = [
    # Std 1
    "Aarav Patel", "Diya Sharma", "Rohan Kumar", "Priya Singh", "Arjun Gupta", "Kavya Mehta",
    # Std 2
    "Vivaan Shah", "Ananya Verma", "Aditya Nair", "Ishika Reddy", "Rehan Pillai", "Anika Joshi",
    # Std 3
    "Siddharth Roy", "Anvi Desai", "Karan Malhotra", "Riya Jain", "Dev Chauhan", "Shruti Iyer",
    # Std 4
    "Dhruv Bose", "Mia Kapoor", "Nikhil Rao", "Sneha Mishra", "Varun Tiwari", "Pooja Pandey",
    # Std 5
    "Rahul Patel", "Neha Singh", "Amit Kumar", "Anjali Mehta", "Vikram Shah", "Ritu Joshi",
    # Std 6
    "Kabir Chandra", "Tanvi Dubey", "Aryan Srivastava", "Meera Nambiar", "Jai Oberoi", "Sana Qureshi",
    # Std 7
    "Pranav Hegde", "Swati Kulkarni", "Akash Garg", "Bhavna Saxena", "Tarun Bhatt", "Divya Sethi",
    # Std 8
    "Surya Pillai", "Anu Krishnan", "Mohit Bansal", "Ritika Ahuja", "Yash Mittal", "Lakshmi Menon",
    # Std 9
    "Rishabh Sinha", "Komal Yadav", "Harish Tripathi", "Sunita Rathore", "Gaurav Choudhary", "Preeti Bajaj",
    # Std 10
    "Abhishek Ghosh", "Nikita Sarkar", "Deepak Bhat", "Pallavi Nair", "Saurabh Jha", "Rupali Sen",
    # Std 11
    "Chirag Thakur", "Vandana Kaur", "Mukesh Rawat", "Neelam Bisht", "Rohit Pathak", "Jyoti Dixit",
    # Std 12
    "Manoj Bhardwaj", "Seema Tyagi", "Rajesh Naik", "Swapna Rao", "Vijay Pillai", "Geeta Nair",
]

def _hash_password(plain: str) -> str:
    return _bcrypt.hashpw(plain.encode('utf-8'), _bcrypt.gensalt()).decode('utf-8')

def _seed_teachers(db):
    emails = ['admin@school.com', 'teacher@gmail.com', 'teacher@school.com', 'admin@gmail.com']
    pw_hash = _hash_password('teacher123')
    for email in emails:
        if db.teachers.count_documents({'email': email}) == 0:
            db.teachers.insert_one({
                'name': 'Dr. Robert Vance' if 'gmail' in email else 'Admin Teacher',
                'email': email,
                'password_hash': pw_hash,
                'created_at': datetime.utcnow()
            })
            print(f"  → Teacher seeded: {email} / teacher123")

def _seed_students(db):
    # Re-seed if Rahul Patel is missing or doesn't have 9876543210
    rahul = db.students.find_one({'name': 'Rahul Patel'})
    if not rahul or rahul.get('mobile') != '9876543210':
        db.students.drop()
        print("  → Re-seeding students to include Rahul Patel (9876543210)")

    if db.students.count_documents({}) == 0:
        pw_hash = _hash_password('student123')
        students = []
        for std in range(1, 13):
            for i in range(1, 7):
                idx = (std - 1) * 6 + (i - 1)
                name = STUDENT_NAMES[idx]
                roll = std * 100 + i
                email = f'student{roll}@school.com'
                mobile = f'98765{std:02d}{i:03d}'

                # Give Rahul Patel exact prompt example values
                if name == "Rahul Patel":
                    roll = 15
                    mobile = "9876543210"
                    email = "rahul@gmail.com"

                students.append({
                    'name': name,
                    'roll_no': roll,
                    'standard': std,
                    'email': email,
                    'mobile': mobile,
                    'password_hash': pw_hash,
                    'created_at': datetime.utcnow()
                })
        db.students.insert_many(students)
        print(f"  → {len(students)} students seeded (password: student123)")
        print(f"     Rahul Patel: mobile=9876543210, std=5, roll=15")
