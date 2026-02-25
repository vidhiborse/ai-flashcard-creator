"""
View all data in the database
"""
from web_app import app
from models import db, User, FlashcardSet, ExamResult, StudySession, ChatMessage
from datetime import datetime

print("="*60)
print("DATABASE VIEWER - AI FLASHCARD CREATOR")
print("="*60)

with app.app_context():
    # View Users
    print("\n👥 USERS:")
    print("-"*60)
    users = User.query.all()
    
    if users:
        for user in users:
            print(f"\n🆔 ID: {user.id}")
            print(f"   Username: {user.username}")
            print(f"   Email: {user.email}")
            print(f"   Created: {user.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   Password Hash: {user.password_hash[:30]}...")
    else:
        print("   No users found")
    
    # View Flashcard Sets
    print("\n\n📚 FLASHCARD SETS:")
    print("-"*60)
    sets = FlashcardSet.query.all()
    
    if sets:
        for s in sets:
            print(f"\n🆔 ID: {s.id}")
            print(f"   User ID: {s.user_id} ({User.query.get(s.user_id).username})")
            print(f"   Name: {s.name}")
            print(f"   Cards: {s.card_count}")
            print(f"   Difficulty: {s.difficulty}")
            print(f"   Created: {s.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        print("   No flashcard sets found")
    
    # View Exam Results
    print("\n\n✍️ EXAM RESULTS:")
    print("-"*60)
    exams = ExamResult.query.all()
    
    if exams:
        for exam in exams:
            print(f"\n🆔 ID: {exam.id}")
            print(f"   User: {User.query.get(exam.user_id).username}")
            print(f"   Exam: {exam.exam_name}")
            print(f"   Score: {exam.score}/{exam.total_questions} ({exam.percentage}%)")
            print(f"   Time: {exam.time_taken}")
            print(f"   Date: {exam.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        print("   No exam results found")
    
    # View Study Sessions
    print("\n\n🔥 STUDY SESSIONS (for streak):")
    print("-"*60)
    sessions = StudySession.query.all()
    
    if sessions:
        for session in sessions:
            print(f"   {User.query.get(session.user_id).username} - {session.activity_type} - {session.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        print("   No study sessions found")
    
    # View Chat Messages
    print("\n\n💬 CHAT MESSAGES:")
    print("-"*60)
    messages = ChatMessage.query.limit(10).all()
    
    if messages:
        print(f"   (Showing first 10 messages)")
        for msg in messages:
            print(f"\n   {User.query.get(msg.user_id).username} ({msg.role}):")
            print(f"   {msg.message[:80]}...")
            print(f"   {msg.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        print("   No chat messages found")
    
    # Summary
    print("\n" + "="*60)
    print("📊 SUMMARY:")
    print("="*60)
    print(f"   Total Users: {User.query.count()}")
    print(f"   Total Flashcard Sets: {FlashcardSet.query.count()}")
    print(f"   Total Exams: {ExamResult.query.count()}")
    print(f"   Total Study Sessions: {StudySession.query.count()}")
    print(f"   Total Chat Messages: {ChatMessage.query.count()}")
    print("="*60)