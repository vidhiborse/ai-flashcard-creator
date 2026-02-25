"""
Database models for user authentication and tracking
Using PostgreSQL for production-ready database
"""
from itsdangerous import URLSafeTimedSerializer
from flask import current_app
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)  # NEW LINE
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    dark_mode = db.Column(db.Boolean, default=False)
    profile_photo = db.Column(db.String(200), nullable=True)
    flashcard_sets = db.relationship('FlashcardSet', backref='user', lazy=True)
    exam_results = db.relationship('ExamResult', backref='user', lazy=True)
    study_sessions = db.relationship('StudySession', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    

    def get_reset_token(self):
        """Generate password reset token"""
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        return s.dumps(self.email, salt='password-reset-salt')
    
    @staticmethod
    def verify_reset_token(token, expires_sec=1800):
        """Verify reset token (valid for 30 minutes)"""
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            email = s.loads(token, salt='password-reset-salt', max_age=expires_sec)
        except:
            return None
        return User.query.filter_by(email=email).first()
    

    def get_stats(self):
        total_flashcards = sum(
            fs.card_count for fs in self.flashcard_sets
        )
        total_exams = len(self.exam_results)
        
        if total_exams > 0:
            avg_score = sum(
                er.percentage for er in self.exam_results
            ) / total_exams
        else:
            avg_score = 0
        
        streak = self.calculate_streak()
        
        return {
            'total_flashcards': total_flashcards,
            'total_exams': total_exams,
            'average_score': round(avg_score, 1),
            'study_streak': streak,
            'total_sets': len(self.flashcard_sets)
        }
    
    def calculate_streak(self):
        if not self.study_sessions:
            return 0
        
        study_dates = sorted(set(
            session.created_at.date()
            for session in self.study_sessions
        ), reverse=True)
        
        if not study_dates:
            return 0
        
        from datetime import date, timedelta
        today = date.today()
        
        if study_dates[0] != today and \
           study_dates[0] != today - timedelta(days=1):
            return 0
        
        streak = 1
        for i in range(len(study_dates) - 1):
            if study_dates[i] - study_dates[i+1] == timedelta(days=1):
                streak += 1
            else:
                break
        
        return streak


class FlashcardSet(db.Model):
    __tablename__ = 'flashcard_sets'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id'), nullable=False
    )
    name = db.Column(db.String(200), nullable=False)
    card_count = db.Column(db.Integer, default=0)
    difficulty = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ExamResult(db.Model):
    __tablename__ = 'exam_results'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id'), nullable=False
    )
    exam_name = db.Column(db.String(200))
    score = db.Column(db.Integer)
    total_questions = db.Column(db.Integer)
    percentage = db.Column(db.Float)
    time_taken = db.Column(db.String(20))
    difficulty = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class StudySession(db.Model):
    __tablename__ = 'study_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    activity_type = db.Column(db.String(50))
    duration_minutes = db.Column(db.Integer, default=0)  # NEW
    flashcard_set_id = db.Column(db.Integer, db.ForeignKey('flashcard_sets.id'), nullable=True)  # NEW
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id'), nullable=False
    )
    role = db.Column(db.String(20))
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    

class PageView(db.Model):
    __tablename__ = 'page_views'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    page = db.Column(db.String(200))
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<PageView {self.page}>'
    
    
    user = db.relationship('User', backref='chat_messages')