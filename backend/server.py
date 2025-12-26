import os
import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from models import db, Student, Teacher, Parent, InternalMark, Assignment, AssignmentSubmission, StudentBehavior, TeacherDepartment, TeacherSection, TeacherSubject, SubjectAttendance, WebhookEvent
import jwt
import bcrypt
from functools import wraps
from ml_app import bp as ml_bp

app = Flask(__name__)
CORS(app)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///erp.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db.init_app(app)

# Register blueprints
app.register_blueprint(ml_bp, url_prefix='/api/ml')

# JWT token required decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        try:
            token = token.split(" ")[1] if " " in token else token
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = data['user']
        except:
            return jsonify({'message': 'Token is invalid'}), 401
        return f(current_user, *args, **kwargs)
    return decorated

# Health check endpoint for Render
@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint for deployment monitoring"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "version": "1.0.0"
    })

# --- API endpoints ---
@app.route("/api/students", methods=["GET"])
@token_required
def get_students(current_user):
    try:
        students = Student.query.all()
        return jsonify([student.to_dict() for student in students])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/students/<roll>", methods=["GET"])
@token_required
def get_student(current_user, roll):
    try:
        student = Student.query.filter_by(roll=roll).first()
        if not student:
            return jsonify({'error': 'Student not found'}), 404
        return jsonify(student.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/teachers", methods=["GET"])
@token_required
def get_teachers(current_user):
    try:
        teachers = Teacher.query.all()
        return jsonify([teacher.to_dict() for teacher in teachers])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/parents", methods=["GET"])
@token_required
def get_parents(current_user):
    try:
        parents = Parent.query.all()
        return jsonify([parent.to_dict() for parent in parents])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/auth/login", methods=["POST"])
def login():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        role = data.get('role', 'student')

        user = None
        if role == 'student':
            user = Student.query.filter_by(username=username).first()
        elif role == 'teacher':
            user = Teacher.query.filter_by(username=username).first()
        elif role == 'parent':
            user = Parent.query.filter_by(username=username).first()

        if user and user.check_password(password):
            token = jwt.encode({
                'user': username,
                'type': role,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
            }, app.config['SECRET_KEY'], algorithm="HS256")

            return jsonify({
                'status': 'ok',
                'username': username,
                'role': role,
                'name': user.name if hasattr(user, 'name') else username,
                'token': token
            })

        return jsonify({'message': 'Invalid credentials'}), 401
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@app.route("/api/subject-attendance", methods=["GET"])
@token_required
def get_subject_attendance(current_user):
    try:
        student_roll = request.args.get('student_roll')
        if not student_roll:
            return jsonify({'error': 'student_roll parameter required'}), 400

        attendances = SubjectAttendance.query.filter_by(student_roll=student_roll).all()
        return jsonify([att.to_dict() for att in attendances])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/assignments", methods=["GET"])
@token_required
def get_assignments(current_user):
    try:
        class_name = request.args.get('class')
        subject = request.args.get('subject')

        query = Assignment.query
        if class_name:
            query = query.filter_by(class_name=class_name)
        if subject:
            query = query.filter_by(subject=subject)

        assignments = query.all()
        return jsonify([assignment.to_dict() for assignment in assignments])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/behavior", methods=["GET"])
@token_required
def get_behavior(current_user):
    try:
        student_roll = request.args.get('student_roll')
        if not student_roll:
            return jsonify({'error': 'student_roll parameter required'}), 400

        behaviors = StudentBehavior.query.filter_by(student_roll=student_roll).all()
        return jsonify([behavior.to_dict() for behavior in behaviors])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/internal-marks", methods=["GET"])
@token_required
def get_internal_marks(current_user):
    try:
        student_roll = request.args.get('student_roll')
        subject = request.args.get('subject')

        query = InternalMark.query
        if student_roll:
            query = query.filter_by(student_roll=student_roll)
        if subject:
            query = query.filter_by(subject=subject)

        marks = query.all()
        return jsonify([mark.to_dict() for mark in marks])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/teacher/<username>/dashboard", methods=["GET"])
@token_required
def get_teacher_dashboard(current_user, username):
    try:
        # Verify the current user matches the requested username
        if current_user != username:
            return jsonify({'error': 'Unauthorized access'}), 403

        # Get teacher info
        teacher = Teacher.query.filter_by(username=username).first()
        if not teacher:
            return jsonify({'error': 'Teacher not found'}), 404

        # Get teacher's sections and subjects
        teacher_sections = TeacherSection.query.filter_by(teacher_username=username).all()
        teacher_subjects = TeacherSubject.query.filter_by(teacher_username=username).all()

        # Get students in teacher's sections
        section_names = [ts.section_name for ts in teacher_sections]
        students_in_sections = Student.query.filter(Student.section.in_(section_names)).all()

        # Calculate stats
        total_students = len(students_in_sections)

        # Calculate average attendance (simplified - using SubjectAttendance)
        attendance_records = []
        for student in students_in_sections:
            student_attendance = SubjectAttendance.query.filter_by(student_roll=student.roll).all()
            if student_attendance:
                avg_attendance = sum(att.attendance_percentage for att in student_attendance) / len(student_attendance)
                attendance_records.append(avg_attendance)

        avg_attendance = sum(attendance_records) / len(attendance_records) if attendance_records else 0

        # Count low attendance students (< 75%)
        low_attendance_count = len([att for att in attendance_records if att < 75])

        # Count at-risk students (simplified - low attendance + behavior issues)
        at_risk_count = low_attendance_count  # For now, just use low attendance count

        # Get recent assignments
        recent_assignments = []
        for subject_rel in teacher_subjects:
            assignments = Assignment.query.filter_by(
                subject=subject_rel.subject_name,
                class_name=subject_rel.class_name
            ).order_by(Assignment.created_at.desc()).limit(3).all()
            recent_assignments.extend([{
                'title': a.title,
                'due_date': a.due_date.isoformat() if a.due_date else None,
                'subject': a.subject,
                'class_name': a.class_name
            } for a in assignments])

        # Get recent behavior records
        recent_behavior = []
        for student in students_in_sections[:10]:  # Check recent 10 students
            behaviors = StudentBehavior.query.filter_by(student_roll=student.roll)\
                .order_by(StudentBehavior.date_recorded.desc()).limit(2).all()
            recent_behavior.extend([{
                'behavior_type': b.behavior_type,
                'date_recorded': b.date_recorded.isoformat(),
                'student_roll': b.student_roll
            } for b in behaviors])

        # Get recent marks
        recent_marks = []
        for subject_rel in teacher_subjects:
            marks = InternalMark.query.filter_by(subject=subject_rel.subject_name)\
                .order_by(InternalMark.date_assessed.desc()).limit(3).all()
            recent_marks.extend([{
                'subject': m.subject,
                'marks_obtained': m.marks_obtained,
                'total_marks': m.total_marks,
                'date_assessed': m.date_assessed.isoformat(),
                'student_roll': m.student_roll
            } for m in marks])

        return jsonify({
            'stats': {
                'total_students': total_students,
                'avg_attendance': round(avg_attendance, 1),
                'low_attendance_count': low_attendance_count,
                'at_risk_count': at_risk_count
            },
            'recent_assignments': recent_assignments[:5],  # Limit to 5 most recent
            'recent_behavior': recent_behavior[:5],
            'recent_marks': recent_marks[:5]
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/teachers/<username>/accessible-students", methods=["GET"])
@token_required
def get_accessible_students(current_user, username):
    try:
        # Verify the current user matches the requested username
        if current_user != username:
            return jsonify({'error': 'Unauthorized access'}), 403

        # Get teacher's sections
        teacher_sections = TeacherSection.query.filter_by(teacher_username=username).all()
        section_names = [ts.section_name for ts in teacher_sections]

        # Get students in those sections
        students = Student.query.filter(Student.section.in_(section_names)).all()

        # Calculate attendance for each student
        student_data = []
        for student in students:
            # Get average attendance across all subjects
            attendance_records = SubjectAttendance.query.filter_by(student_roll=student.roll).all()
            avg_attendance = 0
            if attendance_records:
                avg_attendance = sum(att.attendance_percentage for att in attendance_records) / len(attendance_records)

            student_data.append({
                'roll': student.roll,
                'name': student.name,
                'section': student.section,
                'class': student.class_name,
                'attendance': round(avg_attendance, 1)
            })

        return jsonify(student_data)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Static file serving for frontend
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    if path != "" and os.path.exists(os.path.join(app.root_path, '..', 'frontend', path)):
        return send_from_directory(os.path.join(app.root_path, '..', 'frontend'), path)
    else:
        return send_from_directory(os.path.join(app.root_path, '..', 'frontend'), 'login.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
