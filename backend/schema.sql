-- SQLite database schema for Student Teacher ERP system
-- Using sqlite3 directly (no SQLAlchemy)

-- Students table
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    name TEXT NOT NULL,
    roll TEXT UNIQUE NOT NULL,
    email TEXT NOT NULL,
    class_name TEXT NOT NULL,
    attendance REAL DEFAULT 0.0,
    avg_marks REAL DEFAULT 0.0,
    math_marks REAL DEFAULT 0.0,
    physics_marks REAL DEFAULT 0.0,
    chemistry_marks REAL DEFAULT 0.0,
    cs_marks REAL DEFAULT 0.0,
    english_marks REAL DEFAULT 0.0
);

-- Teachers table
CREATE TABLE IF NOT EXISTS teachers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    department TEXT NOT NULL
);

-- Parents table
CREATE TABLE IF NOT EXISTS parents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    student_roll TEXT NOT NULL,
    FOREIGN KEY (student_roll) REFERENCES students(roll)
);

-- Attendance table (subject-wise attendance)
CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_roll TEXT NOT NULL,
    subject TEXT NOT NULL,
    total_classes INTEGER DEFAULT 0,
    attended_classes INTEGER DEFAULT 0,
    attendance_percentage REAL DEFAULT 0.0,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_roll) REFERENCES students(roll),
    UNIQUE(student_roll, subject)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_students_roll ON students(roll);
CREATE INDEX IF NOT EXISTS idx_students_username ON students(username);
CREATE INDEX IF NOT EXISTS idx_teachers_username ON teachers(username);
CREATE INDEX IF NOT EXISTS idx_parents_username ON parents(username);
CREATE INDEX IF NOT EXISTS idx_parents_student_roll ON parents(student_roll);
CREATE INDEX IF NOT EXISTS idx_attendance_student_roll ON attendance(student_roll);
