"""
Initialize database tables
Run this ONCE to create all tables
"""
from web_app import app
from models import db

print("="*50)
print("INITIALIZING DATABASE")
print("="*50)

with app.app_context():
    print("🗄️  Creating all tables...")
    db.create_all()
    print("✅ All tables created successfully!")
    
    # Show tables
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    
    print(f"\n📊 Created {len(tables)} tables:")
    for table in tables:
        print(f"   ✅ {table}")
    
    print("="*50)
    print("✅ DATABASE READY!")
    print("="*50)