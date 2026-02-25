"""
Backup database to JSON file
"""
from web_app import app
from models import db, User, FlashcardSet, ExamResult, StudySession, ChatMessage
import json
from datetime import datetime

print("="*50)
print("DATABASE BACKUP")
print("="*50)

with app.app_context():
    backup_data = {
        'backup_date': datetime.now().isoformat(),
        'users': [],
        'flashcard_sets': [],
        'exam_results': [],
        'study_sessions': [],
        'chat_messages': []
    }
    
    # Backup users
    users = User.query.all()
    for user in users:
        backup_data['users'].append({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'created_at': user.created_at.isoformat()
        })
    
    # Backup flashcard sets
    sets = FlashcardSet.query.all()
    for s in sets:
        backup_data['flashcard_sets'].append({
            'id': s.id,
            'user_id': s.user_id,
            'name': s.name,
            'card_count': s.card_count,
            'difficulty': s.difficulty,
            'created_at': s.created_at.isoformat()
        })
    
    # Backup exam results
    exams = ExamResult.query.all()
    for exam in exams:
        backup_data['exam_results'].append({
            'id': exam.id,
            'user_id': exam.user_id,
            'exam_name': exam.exam_name,
            'score': exam.score,
            'total_questions': exam.total_questions,
            'percentage': exam.percentage,
            'time_taken': exam.time_taken,
            'created_at': exam.created_at.isoformat()
        })
    
    # Save backup
    filename = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(backup_data, f, indent=2)
    
    print(f"✅ Backup saved: {filename}")
    print(f"✅ Users: {len(backup_data['users'])}")
    print(f"✅ Flashcard Sets: {len(backup_data['flashcard_sets'])}")
    print(f"✅ Exam Results: {len(backup_data['exam_results'])}")
    print("="*50)