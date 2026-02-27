"""
AI Flashcard Creator - Production Ready with PostgreSQL - Vercel Compatible
"""

from PIL import Image
import secrets
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
import os
import tempfile

from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file, flash

from flask_login import (LoginManager, login_user,
                         logout_user, login_required, current_user)
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import google.generativeai as genai
import PyPDF2
import json
from datetime import datetime, timedelta
import csv

from models import (db, User, FlashcardSet,
                    ExamResult, StudySession, ChatMessage, PageView)

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
database_url = os.getenv("DATABASE_URL")
secret_key = os.getenv("SECRET_KEY", "fallback-secret-key")

# Configure Gemini API
genai.configure(api_key=api_key)

app = Flask(__name__)
app.config['SECRET_KEY'] = secret_key

# Email configuration
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True') == 'True'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME', 'noreply@flashcards.com')

mail = Mail(app)

# Fix PostgreSQL URL
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = (
    database_url or 'sqlite:///flashcards.db'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
}

# Vercel compatible paths - use /tmp for writable files
app.config['UPLOAD_FOLDER'] = '/tmp/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

# Create tmp directories (Vercel allows /tmp)
try:
    os.makedirs('/tmp/uploads', exist_ok=True)
    os.makedirs('/tmp/profile_photos', exist_ok=True)
except:
    pass

# Track page views
@app.before_request
def track_page_view():
    """Track every page view in database"""
    if request.path.startswith('/static') or \
       request.path.startswith('/toggle-') or \
       request.path == '/favicon.ico' or \
       request.path == '/favicon.png':
        return
    
    try:
        user_id = current_user.id if current_user.is_authenticated else None
        ip_address = request.remote_addr or 'unknown'
        user_agent = request.headers.get('User-Agent', '')[:500]
        page = request.path
        
        page_view = PageView(
            user_id=user_id,
            page=page,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.session.add(page_view)
        db.session.commit()
    except Exception as e:
        print(f"Tracking error: {e}")
        db.session.rollback()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.after_request
def add_header(response):
    """Add caching headers for static files"""
    if 'Cache-Control' not in response.headers:
        if request.path.startswith('/static/'):
            response.headers['Cache-Control'] = 'public, max-age=3600'
        else:
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
    return response

# ============================================
# HELPER FUNCTIONS
# ============================================
def save_profile_photo(photo):
    """Save and resize profile photo to /tmp"""
    random_hex = secrets.token_hex(8)
    _, file_ext = os.path.splitext(photo.filename)
    photo_filename = random_hex + file_ext
    photo_path = os.path.join('/tmp/profile_photos', photo_filename)
    
    output_size = (300, 300)
    img = Image.open(photo)
    img.thumbnail(output_size)
    img.save(photo_path)
    
    return photo_filename

def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text()
    except Exception as e:
        print(f"Error reading PDF: {e}")
    return text

def extract_text_from_file(filepath):
    file_extension = filepath.lower().split('.')[-1]
    if file_extension == 'pdf':
        return extract_text_from_pdf(filepath)
    elif file_extension in ['txt', 'md']:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    return None

def generate_flashcards(study_text, num_cards=5, difficulty="medium"):
    prompt = f"""
You are an expert teacher creating study flashcards.
Read this study material and create {num_cards} flashcards.
Difficulty level: {difficulty}

STUDY MATERIAL:
{study_text}

FORMAT (follow exactly):
Q1: [question here]
A1: [answer here]

Q2: [question here]
A2: [answer here]

Continue for all {num_cards} questions.
"""
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        return parse_flashcards(response.text)
    except Exception as e:
        print(f"Error generating flashcards: {e}")
        return []

def parse_flashcards(text):
    flashcards = []
    lines = text.strip().split('\n')
    current_question = None
    current_answer = None

    for line in lines:
        line = line.strip()
        if line.startswith('Q') and ':' in line:
            if current_question and current_answer:
                flashcards.append({
                    "question": current_question,
                    "answer": current_answer
                })
            current_question = line.split(':', 1)[1].strip()
            current_answer = None
        elif line.startswith('A') and ':' in line:
            current_answer = line.split(':', 1)[1].strip()

    if current_question and current_answer:
        flashcards.append({
            "question": current_question,
            "answer": current_answer
        })
    return flashcards

def generate_mcq_exam(study_text, num_questions=10, difficulty="medium"):
    prompt = f"""
You are an expert teacher creating a practice exam.
Read this study material and create {num_questions} MCQs.
Difficulty level: {difficulty}

STUDY MATERIAL:
{study_text}

FORMAT (follow EXACTLY):
Q1: [question here]
A) [option A]
B) [option B]
C) [option C]
D) [option D]
CORRECT: [A/B/C/D]

Continue for all {num_questions} questions.

RULES:
- Make wrong options plausible
- Vary correct answer positions
- Test understanding not memorization
"""
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        return parse_mcqs(response.text)
    except Exception as e:
        print(f"Error generating MCQs: {e}")
        return []

def parse_mcqs(text):
    mcqs = []
    lines = text.strip().split('\n')
    current_question = None
    options = {}
    correct_answer = None

    for line in lines:
        line = line.strip()
        if line.startswith('Q') and ':' in line:
            if current_question and len(options) == 4 and correct_answer:
                mcqs.append({
                    "question": current_question,
                    "options": options,
                    "correct": correct_answer
                })
            current_question = line.split(':', 1)[1].strip()
            options = {}
            correct_answer = None
        elif line.startswith(('A)', 'B)', 'C)', 'D)')):
            option_letter = line[0]
            option_text = line.split(')', 1)[1].strip()
            options[option_letter] = option_text
        elif line.startswith('CORRECT:'):
            correct_answer = line.split(':', 1)[1].strip()

    if current_question and len(options) == 4 and correct_answer:
        mcqs.append({
            "question": current_question,
            "options": options,
            "correct": correct_answer
        })
    return mcqs

# ============================================
# AUTH ROUTES
# ============================================
@app.route('/static/sw.js')
def service_worker():
    """Serve service worker with correct MIME type"""
    try:
        response = app.send_static_file('sw.js')
        response.headers['Content-Type'] = 'application/javascript'
        response.headers['Service-Worker-Allowed'] = '/'
        return response
    except:
        return '', 404

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')

        if not username or not email or not password:
            return jsonify({
                'success': False,
                'error': 'All fields are required'
            }), 400

        if User.query.filter_by(username=username).first():
            return jsonify({
                'success': False,
                'error': 'Username already exists'
            }), 400

        if User.query.filter_by(email=email).first():
            return jsonify({
                'success': False,
                'error': 'Email already registered'
            }), 400

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        login_user(user)

        return jsonify({
            'success': True,
            'message': 'Account created successfully!'
        })

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user, remember=True)
            return jsonify({
                'success': True,
                'message': 'Login successful!'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid username or password'
            }), 401

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Request password reset"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        data = request.get_json()
        email = data.get('email')
        
        user = User.query.filter_by(email=email).first()
        
        if user:
            token = user.get_reset_token()
            reset_url = url_for('reset_password', token=token, _external=True)
            
            try:
                msg = Message(
                    'Password Reset Request - AI Flashcard Creator',
                    recipients=[user.email]
                )
                msg.body = f'''Hello {user.username},

To reset your password, click the following link:
{reset_url}

This link will expire in 30 minutes.

If you didn't request this, please ignore this email.

Best regards,
AI Flashcard Creator Team
'''
                mail.send(msg)
                
                return jsonify({
                    'success': True,
                    'message': 'Password reset email sent! Check your inbox.'
                })
            except Exception as e:
                print(f"Email error: {e}")
                return jsonify({
                    'success': False,
                    'error': 'Failed to send email. Please try again.'
                }), 500
        else:
            return jsonify({
                'success': True,
                'message': 'If that email exists, a reset link has been sent.'
            })
    
    return render_template('forgot_password.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password with token"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    user = User.verify_reset_token(token)
    
    if not user:
        return render_template('reset_password.html', expired=True)
    
    if request.method == 'POST':
        data = request.get_json()
        password = data.get('password')
        
        if not password or len(password) < 6:
            return jsonify({
                'success': False,
                'error': 'Password must be at least 6 characters'
            }), 400
        
        user.set_password(password)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Password reset successful! You can now login.'
        })
    
    return render_template('reset_password.html', expired=False)

# ============================================
# MAIN ROUTES
# ============================================

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard with optimized queries"""
    stats = current_user.get_stats()
    
    recent_sets = FlashcardSet.query.filter_by(
        user_id=current_user.id
    ).order_by(FlashcardSet.created_at.desc()).limit(5).all()
    
    recent_exams = ExamResult.query.filter_by(
        user_id=current_user.id
    ).order_by(ExamResult.created_at.desc()).limit(5).all()
    
    exam_history = ExamResult.query.filter_by(
        user_id=current_user.id
    ).order_by(ExamResult.created_at.asc()).limit(10).all()
    
    exam_data = {
        'labels': [e.created_at.strftime('%m/%d') for e in exam_history],
        'scores': [e.percentage for e in exam_history]
    }
    
    return render_template('dashboard.html',
                           stats=stats,
                           recent_sets=recent_sets,
                           recent_exams=recent_exams,
                           exam_data=exam_data)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile page"""
    if request.method == 'POST':
        if 'photo' in request.files:
            action = 'upload_photo'
        else:
            data = request.get_json()
            action = data.get('action')
        
        if action == 'update_info':
            new_username = data.get('username', '').strip()
            new_email = data.get('email', '').strip()
            
            if not new_username or not new_email:
                return jsonify({
                    'success': False,
                    'error': 'Username and email are required'
                }), 400
            
            if new_username != current_user.username:
                existing = User.query.filter_by(username=new_username).first()
                if existing:
                    return jsonify({
                        'success': False,
                        'error': 'Username already taken'
                    }), 400
            
            if new_email != current_user.email:
                existing = User.query.filter_by(email=new_email).first()
                if existing:
                    return jsonify({
                        'success': False,
                        'error': 'Email already registered'
                    }), 400
            
            current_user.username = new_username
            current_user.email = new_email
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Profile updated successfully!'
            })
        
        elif action == 'upload_photo':
            if 'photo' not in request.files:
                return jsonify({
                    'success': False,
                    'error': 'No photo uploaded'
                }), 400
            
            photo = request.files['photo']
            
            if photo.filename == '':
                return jsonify({
                    'success': False,
                    'error': 'No photo selected'
                }), 400
            
            allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
            if '.' not in photo.filename or \
               photo.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
                return jsonify({
                    'success': False,
                    'error': 'Invalid file type. Use PNG, JPG, or GIF'
                }), 400
            
            if current_user.profile_photo:
                old_photo_path = os.path.join('/tmp/profile_photos', 
                                             current_user.profile_photo)
                if os.path.exists(old_photo_path):
                    try:
                        os.remove(old_photo_path)
                    except:
                        pass
            
            photo_filename = save_profile_photo(photo)
            current_user.profile_photo = photo_filename
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Profile photo updated!',
                'photo_url': f'/static/profile_photos/{photo_filename}'
            })
        
        elif action == 'remove_photo':
            if current_user.profile_photo:
                photo_path = os.path.join('/tmp/profile_photos', 
                                         current_user.profile_photo)
                if os.path.exists(photo_path):
                    try:
                        os.remove(photo_path)
                    except:
                        pass
                
                current_user.profile_photo = None
                db.session.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Profile photo removed'
                })
            
            return jsonify({
                'success': True,
                'message': 'No photo to remove'
            })
        
        elif action == 'change_password':
            current_password = data.get('current_password')
            new_password = data.get('new_password')
            
            if not current_user.check_password(current_password):
                return jsonify({
                    'success': False,
                    'error': 'Current password is incorrect'
                }), 400
            
            if len(new_password) < 6:
                return jsonify({
                    'success': False,
                    'error': 'New password must be at least 6 characters'
                }), 400
            
            current_user.set_password(new_password)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Password changed successfully!'
            })
        
        elif action == 'delete_account':
            password = data.get('password')
            
            if not current_user.check_password(password):
                return jsonify({
                    'success': False,
                    'error': 'Incorrect password'
                }), 400
            
            if current_user.profile_photo:
                photo_path = os.path.join('/tmp/profile_photos', 
                                         current_user.profile_photo)
                if os.path.exists(photo_path):
                    try:
                        os.remove(photo_path)
                    except:
                        pass
            
            FlashcardSet.query.filter_by(user_id=current_user.id).delete()
            ExamResult.query.filter_by(user_id=current_user.id).delete()
            StudySession.query.filter_by(user_id=current_user.id).delete()
            ChatMessage.query.filter_by(user_id=current_user.id).delete()
            
            db.session.delete(current_user)
            db.session.commit()
            
            logout_user()
            
            return jsonify({
                'success': True,
                'message': 'Account deleted successfully'
            })
    
    stats = current_user.get_stats()
    return render_template('profile.html', stats=stats)

@app.route('/analytics')
@login_required
def analytics():
    """Advanced analytics dashboard"""
    from sqlalchemy import func, extract
    
    today = datetime.utcnow().date()
    ninety_days_ago = today - timedelta(days=90)
    
    sessions = StudySession.query.filter(
        StudySession.user_id == current_user.id,
        StudySession.created_at >= ninety_days_ago
    ).all()
    
    heatmap_data = {}
    for session in sessions:
        date_key = session.created_at.strftime('%Y-%m-%d')
        heatmap_data[date_key] = heatmap_data.get(date_key, 0) + 1
    
    thirty_days_ago = today - timedelta(days=30)
    daily_time = db.session.query(
        func.date(StudySession.created_at).label('date'),
        func.sum(StudySession.duration_minutes).label('total_minutes')
    ).filter(
        StudySession.user_id == current_user.id,
        StudySession.created_at >= thirty_days_ago
    ).group_by(func.date(StudySession.created_at)).all()
    
    time_per_day = {
        'labels': [d.date.strftime('%m/%d') if d.date else '' for d in daily_time],
        'data': [d.total_minutes or 0 for d in daily_time]
    }
    
    difficulty_stats = db.session.query(
        ExamResult.difficulty,
        func.avg(ExamResult.percentage).label('avg_score'),
        func.count(ExamResult.id).label('count')
    ).filter(
        ExamResult.user_id == current_user.id
    ).group_by(ExamResult.difficulty).all()
    
    difficulty_data = {
        'labels': [d.difficulty or 'Unknown' for d in difficulty_stats],
        'scores': [round(d.avg_score, 1) if d.avg_score else 0 for d in difficulty_stats],
        'counts': [d.count for d in difficulty_stats]
    }
    
    set_performance = db.session.query(
        FlashcardSet.name,
        func.avg(ExamResult.percentage).label('avg_score'),
        func.count(ExamResult.id).label('exam_count')
    ).join(
        ExamResult,
        ExamResult.user_id == current_user.id
    ).filter(
        FlashcardSet.user_id == current_user.id
    ).group_by(FlashcardSet.name).all()
    
    sorted_sets = sorted(
        [(s.name, s.avg_score or 0, s.exam_count) for s in set_performance],
        key=lambda x: x[1],
        reverse=True
    )
    
    best_sets = sorted_sets[:5] if len(sorted_sets) > 0 else []
    worst_sets = sorted_sets[-5:][::-1] if len(sorted_sets) > 5 else []
    
    hourly_activity = db.session.query(
        extract('hour', StudySession.created_at).label('hour'),
        func.count(StudySession.id).label('count')
    ).filter(
        StudySession.user_id == current_user.id
    ).group_by(extract('hour', StudySession.created_at)).all()
    
    hour_data = {hour: 0 for hour in range(24)}
    for activity in hourly_activity:
        if activity.hour is not None:
            hour_data[int(activity.hour)] = activity.count
    
    total_study_time = sum(s.duration_minutes or 0 for s in sessions)
    total_sessions = len(sessions)
    avg_session_length = total_study_time / total_sessions if total_sessions > 0 else 0
    
    return render_template('analytics.html',
                           heatmap_data=heatmap_data,
                           time_per_day=time_per_day,
                           difficulty_data=difficulty_data,
                           best_sets=best_sets,
                           worst_sets=worst_sets,
                           hour_data=hour_data,
                           total_study_time=total_study_time,
                           total_sessions=total_sessions,
                           avg_session_length=round(avg_session_length, 1))

@app.route('/toggle-dark-mode', methods=['POST'])
@login_required
def toggle_dark_mode():
    """Toggle dark mode preference"""
    current_user.dark_mode = not current_user.dark_mode
    db.session.commit()
    return jsonify({
        'success': True,
        'dark_mode': current_user.dark_mode
    })

@app.route('/study')
@login_required
def study():
    return render_template('study.html')

@app.route('/generate', methods=['POST'])
@login_required
def generate():
    try:
        if 'file' not in request.files:
            return jsonify({
                'success': False, 'error': 'No file uploaded'
            }), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'success': False, 'error': 'No file selected'
            }), 400

        num_cards = int(request.form.get('num_cards', 5))
        difficulty = request.form.get('difficulty', 'medium')
        set_name = request.form.get(
            'set_name',
            f'Study Set - {datetime.now().strftime("%Y-%m-%d")}'
        )

        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        study_text = extract_text_from_file(filepath)

        if not study_text or len(study_text) < 50:
            return jsonify({
                'success': False,
                'error': 'Could not extract enough text from file'
            }), 400

        flashcards = generate_flashcards(study_text, num_cards, difficulty)

        if not flashcards:
            return jsonify({
                'success': False,
                'error': 'Failed to generate flashcards'
            }), 500

        flashcard_set = FlashcardSet(
            user_id=current_user.id,
            name=set_name,
            card_count=len(flashcards),
            difficulty=difficulty
        )
        db.session.add(flashcard_set)

        session = StudySession(
            user_id=current_user.id,
            activity_type='flashcard'
        )
        db.session.add(session)
        db.session.commit()

        with open('/tmp/last_flashcards.json', 'w') as f:
            json.dump(flashcards, f)

        with open('/tmp/last_study_text.txt', 'w', encoding='utf-8') as f:
            f.write(study_text)

        return jsonify({
            'success': True,
            'flashcards': flashcards,
            'count': len(flashcards)
        })

    except Exception as e:
        print(f"Generate error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/generate-exam', methods=['POST'])
@login_required
def generate_exam():
    try:
        num_questions = int(request.form.get('num_questions', 10))
        difficulty = request.form.get('difficulty', 'medium')

        try:
            with open('/tmp/last_study_text.txt', 'r', encoding='utf-8') as f:
                study_text = f.read()
        except FileNotFoundError:
            return jsonify({
                'success': False,
                'error': 'Please upload a file first!'
            }), 400

        if not study_text or len(study_text) < 50:
            return jsonify({
                'success': False,
                'error': 'Not enough study material'
            }), 400

        mcqs = generate_mcq_exam(study_text, num_questions, difficulty)

        if not mcqs:
            return jsonify({
                'success': False,
                'error': 'Failed to generate exam'
            }), 500

        with open('/tmp/last_exam.json', 'w') as f:
            json.dump(mcqs, f)

        return jsonify({
            'success': True,
            'mcqs': mcqs,
            'count': len(mcqs)
        })

    except Exception as e:
        print(f"Generate exam error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/submit-exam', methods=['POST'])
@login_required
def submit_exam():
    try:
        data = request.get_json()
        user_answers = data.get('answers', {})
        time_taken = data.get('time_taken', '0:00')

        with open('/tmp/last_exam.json', 'r') as f:
            mcqs = json.load(f)

        total = len(mcqs)
        correct_count = 0
        results = []

        for i, mcq in enumerate(mcqs):
            question_num = str(i)
            user_answer = user_answers.get(question_num, '')
            correct_answer = mcq['correct']
            is_correct = user_answer == correct_answer

            if is_correct:
                correct_count += 1

            results.append({
                'question': mcq['question'],
                'user_answer': user_answer,
                'correct_answer': correct_answer,
                'is_correct': is_correct,
                'options': mcq['options']
            })

        score_percentage = (
            (correct_count / total) * 100 if total > 0 else 0
        )

        exam_result = ExamResult(
            user_id=current_user.id,
            exam_name=f'Exam - {datetime.now().strftime("%Y-%m-%d %H:%M")}',
            score=correct_count,
            total_questions=total,
            percentage=score_percentage,
            time_taken=time_taken,
            difficulty='medium'
        )
        db.session.add(exam_result)

        session = StudySession(
            user_id=current_user.id,
            activity_type='exam'
        )
        db.session.add(session)
        db.session.commit()

        return jsonify({
            'success': True,
            'score': correct_count,
            'total': total,
            'percentage': round(score_percentage, 1),
            'results': results
        })

    except Exception as e:
        print(f"Submit exam error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/download/<format>')
@login_required
def download(format):
    try:
        with open('/tmp/last_flashcards.json', 'r') as f:
            flashcards = json.load(f)

        if format == 'txt':
            filename = '/tmp/flashcards.txt'
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("="*50 + "\n")
                f.write("YOUR AI-GENERATED FLASHCARDS\n")
                f.write("="*50 + "\n\n")
                for i, card in enumerate(flashcards, 1):
                    f.write(f"CARD {i}\n")
                    f.write(f"Q: {card['question']}\n")
                    f.write(f"A: {card['answer']}\n")
                    f.write("-"*50 + "\n\n")
            return send_file(filename, as_attachment=True, download_name='flashcards.txt')

        elif format == 'json':
            filename = '/tmp/flashcards.json'
            with open(filename, 'w') as f:
                json.dump(flashcards, f, indent=2)
            return send_file(filename, as_attachment=True, download_name='flashcards.json')

        else:
            return "Invalid format", 400

    except Exception as e:
        print(f"Download error: {e}")
        return str(e), 500

# ============================================
# AI STUDY BUDDY ROUTES
# ============================================

@app.route('/chat')
@login_required
def chat():
    messages = ChatMessage.query.filter_by(
        user_id=current_user.id
    ).order_by(ChatMessage.created_at.desc()).limit(50).all()
    messages = list(reversed(messages))
    return render_template('chat.html', messages=messages)

@app.route('/api/chat', methods=['POST'])
@login_required
def send_chat_message():
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        action = data.get('action', 'chat')

        if not user_message:
            return jsonify({
                'success': False,
                'error': 'Message cannot be empty'
            }), 400

        user_chat = ChatMessage(
            user_id=current_user.id,
            role='user',
            message=user_message
        )
        db.session.add(user_chat)
        db.session.commit()

        study_context = ""
        try:
            with open('/tmp/last_study_text.txt', 'r', encoding='utf-8') as f:
                study_context = f.read()[:2000]
        except:
            study_context = ""

        recent_messages = ChatMessage.query.filter_by(
            user_id=current_user.id
        ).order_by(ChatMessage.created_at.desc()).limit(10).all()

        chat_history = ""
        for msg in reversed(recent_messages[1:]):
            chat_history += f"{msg.role}: {msg.message}\n"

        if action == 'explain':
            system_prompt = f"""You are a helpful study buddy and tutor.
Study Material Context: {study_context}
Previous conversation: {chat_history}
Explain this concept simply with examples and analogies."""

        elif action == 'quiz':
            system_prompt = f"""You are a quiz master.
Study Material: {study_context if study_context else "General knowledge"}
Ask ONE challenging but fair question. After they answer, explain."""

        elif action == 'flashcards':
            system_prompt = f"""You are a flashcard creator.
Suggest 5 key flashcard questions.
Format:
1. Q: [Question] | A: [Answer]
Make questions test understanding."""

        else:
            system_prompt = f"""You are an AI study buddy.
Study Material Context: {study_context}
Previous conversation: {chat_history}
Guidelines:
- Be friendly and encouraging
- Explain concepts clearly
- Keep responses concise (2-3 paragraphs max)"""

        full_prompt = (
            f"{system_prompt}\n\n"
            f"Student: {user_message}\n\n"
            f"AI Study Buddy:"
        )

        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(full_prompt)

        ai_response = response.text

        ai_chat = ChatMessage(
            user_id=current_user.id,
            role='assistant',
            message=ai_response
        )
        db.session.add(ai_chat)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': ai_response,
            'timestamp': ai_chat.created_at.strftime('%I:%M %p')
        })

    except Exception as e:
        print(f"Chat error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/chat/clear', methods=['POST'])
@login_required
def clear_chat():
    try:
        ChatMessage.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/chat/export', methods=['GET'])
@login_required
def export_chat():
    try:
        messages = ChatMessage.query.filter_by(
            user_id=current_user.id
        ).order_by(ChatMessage.created_at.asc()).all()

        filename = '/tmp/chat_history.txt'
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("=" * 50 + "\n")
            f.write("AI STUDY BUDDY CHAT HISTORY\n")
            f.write(f"User: {current_user.username}\n")
            f.write("=" * 50 + "\n\n")
            for msg in messages:
                timestamp = msg.created_at.strftime('%Y-%m-%d %I:%M %p')
                role = "You" if msg.role == "user" else "AI Study Buddy"
                f.write(f"[{timestamp}] {role}:\n")
                f.write(f"{msg.message}\n")
                f.write("-" * 50 + "\n\n")

        return send_file(filename, as_attachment=True, download_name='chat_history.txt')
    except Exception as e:
        print(f"Export chat error: {e}")
        return str(e), 500

@app.route('/admin')
@login_required
def admin():
    """Enhanced admin page with visitor stats"""
    
    if current_user.id != 1:
        flash('Access denied. Admin only.')
        return redirect(url_for('dashboard'))
    
    from sqlalchemy import func, distinct
    
    all_users = User.query.order_by(User.created_at.desc()).all()
    user_stats = []
    for user in all_users:
        stats = user.get_stats()
        user_stats.append({
            'user': user,
            'stats': stats
        })
    
    total_users = len(all_users)
    total_flashcards = sum(s['stats']['total_flashcards'] for s in user_stats)
    total_exams = sum(s['stats']['total_exams'] for s in user_stats)
    
    today = datetime.utcnow().date()
    
    total_page_views = PageView.query.count()
    
    unique_visitors = db.session.query(
        func.count(distinct(PageView.ip_address))
    ).scalar() or 0
    
    today_views = PageView.query.filter(
        func.date(PageView.created_at) == today
    ).count()
    
    week_ago = today - timedelta(days=7)
    week_views = PageView.query.filter(
        PageView.created_at >= week_ago
    ).count()
    
    popular_pages = db.session.query(
        PageView.page,
        func.count(PageView.id).label('count')
    ).group_by(PageView.page).order_by(
        func.count(PageView.id).desc()
    ).limit(10).all()
    
    recent_visitors = PageView.query.order_by(
        PageView.created_at.desc()
    ).limit(20).all()
    
    return render_template('admin.html',
                           user_stats=user_stats,
                           total_users=total_users,
                           total_flashcards=total_flashcards,
                           total_exams=total_exams,
                           total_page_views=total_page_views,
                           unique_visitors=unique_visitors,
                           today_views=today_views,
                           week_views=week_views,
                           popular_pages=popular_pages,
                           recent_visitors=recent_visitors)

@app.route('/api/stats')
@login_required
def get_stats():
    stats = current_user.get_stats()
    return jsonify(stats)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("✅ Database tables created!")

    print("""
    ╔══════════════════════════════════════════════╗
    ║   AI FLASHCARD CREATOR - PRODUCTION READY    ║
    ║   PostgreSQL + Responsive Design             ║
    ╚══════════════════════════════════════════════╝

    🌐 Server starting...
    🗄️  Database: PostgreSQL (Neon)
    🚀 Ready!
    """)
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)