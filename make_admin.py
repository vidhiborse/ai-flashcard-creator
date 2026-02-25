"""
Make a user an admin
"""
from web_app import app
from models import db, User

with app.app_context():
    username = input("Enter username to make admin: ")
    user = User.query.filter_by(username=username).first()
    
    if user:
        print(f"✅ Found user: {user.username} (ID: {user.id})")
        print(f"   Email: {user.email}")
        confirm = input("Make this user admin? (yes/no): ")
        if confirm.lower() == 'yes':
            # Add is_admin column later, for now just show their ID
            print(f"✅ User ID is: {user.id}")
            print(f"Update web_app.py admin route:")
            print(f"   if current_user.id != {user.id}:")
    else:
        print(f"❌ User '{username}' not found")