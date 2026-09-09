# Professional Student Management System

A complete full-stack real-world web application built for school administration. This system uses **Python Flask** on the backend and **MongoDB** as the core database, with a **Vanilla JS/HTML/CSS** frontend.

## 🚀 Features

### Core Capabilities
- **Role-Based Authentication**: Secure JWT-based access separating Teachers from Students.
- **Strict Data Isolation**: Enforced Standard-level security on the backend. Teachers actively work within *one* standard at a time.
- **MongoDB NoSQL Store**: robust storage structure storing nested documents and referenced patterns efficiently.
- **Dynamic Routing**: Single-page-app-like client experience built purely with Vanilla JS, API interceptors, and JWT localStorage handling.

### 👨‍🏫 Teacher Portal
- **Dashboard**: Live student metrics, standard summary, attendance, and result percentage indicators.
- **Standard Selector**: Required flow (Login -> Select Standard -> Dashboard) to enforce data boundaries.
- **Student Directory**: Full CRUD functionality inside the selected standard.
- **Date-wise Attendance**: Can go back and mark attendance for any past dates.
- **Exam Results**: Grading, passing logic, percentage, and results generation.

### 👨‍🎓 Student Portal
- **Mobile Login**: Secure student authentication using 10-digit mobile number and password (Roll Number is kept separate for school record).
- **Personal Dashboard**: Only view their own profile, attendance summary, and results. No other student's data is accessible.
- **Attendance & Results History**: Full transparent access.

---

## 🛠️ Technology Stack

**Frontend:**
- HTML5, CSS3, Vanilla JavaScript
- Modern custom CSS framework + responsive layout (No React/Angular)
- Client-side token storage & UI state management

**Backend:**
- **Python 3**
- **Flask**: lightweight API server
- **Flask-JWT-Extended**: for secure Bearer tokens
- **PyMongo**: native MongoDB client driver
- **bcrypt**: secure password hashing (no plaintext!)
- **Flask-CORS**: cross-origin safety
- **python-dotenv**: environment secret management

**Database:**
- **MongoDB** (Default: `localhost:27017` / Database: `student_management`)

---

## 📂 Project Folder Structure

```
c:\STUDENT_MANAGMENT\
├── backend/
│   ├── app.py                  ← Main Flask entry point (factory + routing)
│   ├── config.py               ← App configs loaded from .env
│   ├── requirements.txt        ← Python dependencies
│   ├── .env                    ← Environment variables (Secrets & DB URI)
│   │
│   ├── database/
│   │   └── db.py               ← PyMongo connection & Auto-Seeder
│   │
│   ├── middleware/
│   │   └── auth_middleware.py  ← JWT decorators & Standard Validation
│   │
│   ├── models/
│   │   ├── student_model.py    ← Queries for finding & updating students
│   │   ├── teacher_model.py    ← Teacher auth queries
│   │   ├── attendance_model.py ← Aggregations and date-wise DB ops
│   │   └── result_model.py     ← Exam grading calculation queries
│   │
│   └── routes/
│       ├── auth_routes.py      ← POST logins
│       ├── student_routes.py   ← Student CRUD
│       ├── teacher_routes.py   ← Dashboard Stats & standard list
│       ├── attendance_routes.py← Attendance saving & history
│       └── result_routes.py    ← Exam saving & history
│
├── frontend/
│   ├── index.html              ← Landing Page & Portal Selection
│   │
│   ├── teacher/
│   │   ├── login.html          ← Teacher secure login
│   │   ├── select-standard.html← The mandatory standard gate
│   │   ├── dashboard.html      
│   │   ├── students.html       
│   │   ├── add-student.html    
│   │   ├── edit-student.html   
│   │   ├── attendance.html     ← Dual layout: history + mark attendance
│   │   └── results.html        
│   │
│   ├── student/
│   │   ├── login.html          ← Mobile + Password logic
│   │   ├── dashboard.html      
│   │   ├── profile.html        
│   │   ├── attendance.html     
│   │   └── result.html         
│   │
│   ├── css/
│   │   ├── style.css           ← Global layout, buttons, forms, sidebar
│   │   ├── login.css           
│   │   └── dashboard.css       
│   │
│   └── js/
│       ├── api.js              ← Core HTTP Fetch wrapper with auto-auth
│       ├── auth.js             ← Session guard & JWT parser
│       ├── standard.js         ← Active Standard state engine
│       ├── teacher.js          
│       ├── student.js          
│       ├── attendance.js       
│       └── result.js           
└── README.md
```

---

## ⚙️ Installation & Setup

1. **Clone the repository** (if not already local)
2. **Install & start MongoDB**
   - Ensure MongoDB is running locally on port `27017`.

3. **Backend Setup**
   ```powershell
   cd backend
   python -m venv venv
   .\venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. **Environment Variables**
   Make sure `backend/.env` contains:
   ```env
   MONGO_URI=mongodb://localhost:27017/
   DATABASE_NAME=student_management
   JWT_SECRET_KEY=super_secret_jwt_key_12345
   FLASK_ENV=development
   FLASK_APP=app.py
   ```

5. **Run the Application**
   ```powershell
   python app.py
   ```
   *The server runs on http://localhost:5000 and dynamically serves both the APIs (`/api/*`) and the static Frontend HTML.*

6. **Open in Browser**
   - Go to: **[http://localhost:5000](http://localhost:5000)**

---

## 🔑 Demo Data & Credentials

Upon first run, the `database/db.py` seeder automatically initializes your MongoDB with 1 Teacher and 72 Students (6 per standard).

### Teacher
- **Email:** `admin@school.com`
- **Password:** `teacher123`

### Students (Standard 1 to 12)
- **Mobile Number:** `9876505001` (Example for Standard 5, Student 1)
- **Password:** `student123`
*(Mobile Pattern: `98765` + `01-12 (Standard)` + `001-006 (Student)`)*

---

## 🚨 Troubleshooting

- **MongoDB Errors:** Ensure the Mongo service is running. Check Task Manager / Services for `MongoDB`.
- **401 Unauthorized:** Your JWT may have expired. Relog via the main page.
- **400 Standard Error:** Attempting to manipulate routes bypassing the Active Standard UI. Return to *Select Standard*.

*Built to represent a professional, realistic architecture for BCA portfolios and complete full-stack learning.*
