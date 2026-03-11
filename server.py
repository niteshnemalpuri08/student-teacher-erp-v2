from flask import Flask, request, jsonify, send_from_directory, send_file, make_response
from flask_cors import CORS
from models import db, User, Attendance, StudentPerformance, Message
from notifier import send_absent_email, send_absent_sms, send_payment_receipt
from datetime import date, datetime
import io
import stripe
import base64
import numpy as np
import cv2
import os
import sys
import pytesseract
from PIL import Image
import re
from werkzeug.utils import secure_filename
from predictor import predict_score 
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# --- 1. APP CONFIGURATION ---
# Based on your screenshots, your HTML files are inside this path:
app = Flask(__name__, 
            static_folder='AI-Powered Student Attendance/final_complete_project', 
            static_url_path='')

CORS(app, resources={r"/*": {"origins": "*"}}) 

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///school.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'super_secret'
UPLOAD_FOLDER = 'uploads/payments'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Stripe Secret Key
stripe.api_key = "sk_test_YOUR_STRIPE_SECRET_KEY" 

db.init_app(app)

# --- 2. OCR / IMAGE PROCESSING SETUP ---
try:
    if sys.platform == 'win32':
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    else:
        pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'
    OCR_AVAILABLE = True
except:
    OCR_AVAILABLE = False

# --- 3. AI FACE RECOGNITION SETUP ---
face_recognizer = None
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
AI_READY = False
FACE_SIZE = (200, 200)

def process_face(img_gray):
    equalized = cv2.equalizeHist(img_gray)
    resized = cv2.resize(equalized, FACE_SIZE)
    return resized

def train_ai():
    global AI_READY, face_recognizer
    try:
        face_dir = os.path.join(os.getcwd(), "faces", "24cse001")
        if not os.path.exists(face_dir):
            print("⚠️ Skipping AI training: No photos found.")
            return

        face_recognizer = cv2.face.LBPHFaceRecognizer_create()
        face_samples, ids = [], []
        
        for filename in os.listdir(face_dir):
            if filename.lower().endswith((".jpg", ".png", ".jpeg")):
                img = cv2.imread(os.path.join(face_dir, filename))
                if img is None: continue
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(gray, 1.1, 4)
                for (x, y, w, h) in faces:
                    face_roi = process_face(gray[y:y+h, x:x+w])
                    face_samples.append(face_roi)
                    ids.append(1) 
        
        if len(face_samples) > 0:
            face_recognizer.train(face_samples, np.array(ids))
            AI_READY = True
            print("✅ AI Trained successfully.")
    except Exception as e:
        print(f"⚠️ AI training error: {e}")

# =================================================================
# 🛡️ AUTH & LOGIN ROUTES
# =================================================================

@app.route('/')
def serve_index(): 
    return send_from_directory(app.static_folder, 'login.html')

@app.route('/auth/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS': return jsonify({'success': True}), 200
    data = request.json
    user = User.query.filter_by(username=data['username']).first()
    if user and user.password == data['password']:
        return jsonify({'success': True, 'role': user.role, 'username': user.username, 'name': user.name, 'section': user.section})
    return jsonify({'success': False, 'message': 'Invalid credentials'}), 401

@app.route('/auth/face_login', methods=['POST'])
def face_login():
    if not AI_READY: return jsonify({'success': False, 'message': 'AI System Not Ready'})
    try:
        data = request.json
        image_data = data['image'].split(',')[1]
        img_bytes = base64.decodebytes(image_data.encode())
        img = cv2.imdecode(np.frombuffer(img_bytes, np.uint8), cv2.IMREAD_COLOR)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        for (x, y, w, h) in faces:
            roi_gray = process_face(gray[y:y+h, x:x+w])
            label, confidence = face_recognizer.predict(roi_gray)
            if confidence < 70:
                user = User.query.filter_by(username="24cse001").first()
                if user: return jsonify({'success': True, 'role': user.role, 'username': user.username, 'name': user.name, 'section': user.section})
        return jsonify({'success': False, 'message': 'Face Not Recognized'})
    except Exception as e: return jsonify({'success': False, 'message': str(e)})

# =================================================================
# 🏫 TEACHER & STUDENT ROUTES
# =================================================================

@app.route('/api/teacher/students', methods=['POST'])
def get_teacher_students():
    data = request.json
    teacher = User.query.filter_by(username=data.get('username')).first()
    if not teacher or teacher.role != 'teacher': return jsonify({'error': 'Unauthorized'}), 401
    students = User.query.filter_by(role='student', section=teacher.section).all()
    result = [{'roll': s.username, 'name': s.name, 'attendance': s.performance.attendance if s.performance else 0} for s in students]
    return jsonify({'section': teacher.section, 'students': result})

@app.route('/api/attendance/bulk', methods=['POST'])
def bulk_att():
    data = request.json
    for item in data.get('attendance', []):
        user = User.query.filter_by(username=item['roll']).first()
        if user and user.performance:
            if item['present']: user.performance.attendance = min(100, user.performance.attendance + 0.5)
            else: user.performance.attendance = max(0, user.performance.attendance - 1.5)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/students/<username>', methods=['GET'])
def get_student_data(username):
    user = User.query.filter_by(username=username).first()
    if not user or not user.performance: return jsonify({'error': 'No data'}), 404
    p = user.performance
    return jsonify({'name': user.name, 'roll': user.username, 'attendance': p.attendance, 'avg_marks': p.avg_marks})

# =================================================================
# 💰 PAYMENT & CHAT ROUTES
# =================================================================

@app.route('/api/payment/upload_proof', methods=['POST'])
def upload_payment_proof():
    try:
        username, txn_id = request.form.get('username'), request.form.get('txn_id')
        file = request.files.get('screenshot')
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
        file.save(file_path)
        # Simplified PDF Generation
        buffer = io.BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=letter)
        pdf.drawString(100, 750, f"Receipt for {username} - TXN: {txn_id}")
        pdf.save()
        buffer.seek(0)
        return jsonify({'success': True, 'message': 'Receipt Processed'})
    except Exception as e: return jsonify({'success': False, 'message': str(e)})

@app.route('/api/chat/history', methods=['POST'])
def get_chat_history():
    data = request.json
    u1, u2 = data.get('user1'), data.get('user2')
    msgs = Message.query.filter(((Message.sender == u1) & (Message.receiver == u2)) | ((Message.sender == u2) & (Message.receiver == u1))).all()
    return jsonify([{'sender': m.sender, 'content': m.content} for m in msgs])

# =================================================================
# 🛠️ SYSTEM MAINTENANCE
# =================================================================

@app.route('/repair_data')
def repair_data():
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username='t01').first():
            db.session.add(User(username='t01', password='password', role='teacher', name='Prof. Sharma', section='A'))
        db.session.commit()
    return "✅ Data Repaired"

@app.route('/<path:path>')
def serve_static(path): 
    return send_from_directory(app.static_folder, path)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        train_ai()
    app.run(host='0.0.0.0', port=5000)