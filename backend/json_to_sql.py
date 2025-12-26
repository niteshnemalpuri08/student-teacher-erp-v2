import json
import os
from datetime import datetime, date
from flask import Flask
from models import db, Student, Teacher, TeacherSection, TeacherSubject, TeacherDepartment, SubjectAttendance, InternalMark

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///school_management.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app

def load_json_data():
    """Load data from JSON files"""
    data_dir = os.path.join(os.path.dirname(__file__), 'data')

    # Load teachers data
    teachers_file = os.path.join(data_dir, 'teachers.json')
    with open(teachers_file, 'r') as f:
        teachers_data = json.load(f)

    # Load students data
    students_file = os.path.join(data_dir, 'students.json')
    with open(students_file, 'r') as f:
        students_data = json.load(f)

    return teachers_data, students_data

def convert_json_to_sql():
    """Convert JSON data to SQL database"""
    app = create_app()

    with app.app_context():
        # Create all tables
        db.create_all()

        # Load JSON data
        teachers_data, students_data = load_json_data()

        print("Converting teachers data...")

        # Convert teachers
        for teacher_data in teachers_data:
            # Check if teacher already exists
            existing_teacher = Teacher.query.filter_by(username=teacher_data['username']).first()
            if existing_teacher:
                print(f"Teacher {teacher_data['username']} already exists, skipping...")
                continue

            # Create teacher
            teacher = Teacher(
                username=teacher_data['username'],
                password=teacher_data['password'],  # Note: In production, this should be hashed
                name=teacher_data['name'],
                email=teacher_data['email'],
                department=teacher_data['department']
            )
            db.session.add(teacher)

            # Create teacher department relationship
            teacher_dept = TeacherDepartment(
                teacher_username=teacher_data['username'],
                department=teacher_data['department'],
                assigned_date=date.today()
            )
            db.session.add(teacher_dept)

            # Create teacher section (assuming section A for all)
            teacher_section = TeacherSection(
                teacher_username=teacher_data['username'],
                section='A',
                class_name='B.Tech CSE 2024',
                assigned_date=date.today()
            )
            db.session.add(teacher_section)

            # Create teacher subjects (assuming common subjects)
            subjects = ['Mathematics', 'Physics', 'Chemistry', 'Computer Science', 'English']
            for subject in subjects:
                teacher_subject = TeacherSubject(
                    teacher_username=teacher_data['username'],
                    subject=subject,
                    class_name='B.Tech CSE 2024',
                    section='A',
                    assigned_date=date.today()
                )
                db.session.add(teacher_subject)

        print("Converting students data...")

        # Convert students
        for student_data in students_data:
            # Check if student already exists
            existing_student = Student.query.filter_by(roll=student_data['roll']).first()
            if existing_student:
                print(f"Student {student_data['roll']} already exists, skipping...")
                continue

            # Create student
            student = Student(
                username=student_data['username'],
                password_hash=student_data['password'],  # Note: This should be properly hashed
                name=student_data['name'],
                roll=student_data['roll'],
                email=student_data['email'],
                class_name=student_data['class'],
                attendance=student_data['attendance'],
                avg_marks=student_data['avg_marks'],
                math_marks=student_data['marks']['math'],
                physics_marks=student_data['marks']['physics'],
                chemistry_marks=student_data['marks']['chemistry'],
                cs_marks=student_data['marks']['cs'],
                english_marks=student_data['marks']['english']
            )
            db.session.add(student)

            # Create subject attendance records
            subjects = ['Mathematics', 'Physics', 'Chemistry', 'Computer Science', 'English']
            cs_marks = student_data['marks']['cs']  # Assuming cs_marks represents attendance percentage

            for subject in subjects:
                # Create subject attendance with some variation
                attendance_percentage = min(100, max(60, cs_marks + (student_data['attendance'] - 80)))
                total_classes = 50  # Assuming 50 classes per subject
                attended_classes = int((attendance_percentage / 100) * total_classes)

                subject_attendance = SubjectAttendance(
                    student_roll=student_data['roll'],
                    subject=subject,
                    total_classes=total_classes,
                    attended_classes=attended_classes,
                    attendance_percentage=attendance_percentage
                )
                db.session.add(subject_attendance)

            # Create internal marks records
            for subject, marks in student_data['marks'].items():
                subject_name = {
                    'math': 'Mathematics',
                    'physics': 'Physics',
                    'chemistry': 'Chemistry',
                    'cs': 'Computer Science',
                    'english': 'English'
                }.get(subject, subject)

                internal_mark = InternalMark(
                    student_roll=student_data['roll'],
                    subject=subject_name,
                    assessment_type='Mid-term',
                    marks=marks,
                    max_marks=100,
                    date_assessed=date.today(),
                    teacher_username='t01'  # Assign to first teacher
                )
                db.session.add(internal_mark)

        # Commit all changes
        try:
            db.session.commit()
            print("✅ Successfully converted JSON data to SQL database!")
            print(f"✅ Added {len(teachers_data)} teachers")
            print(f"✅ Added {len(students_data)} students")
            print("✅ Created teacher-section and teacher-subject relationships")
            print("✅ Created subject attendance records")
            print("✅ Created internal marks records")

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error during conversion: {str(e)}")
            raise

if __name__ == "__main__":
    convert_json_to_sql()
