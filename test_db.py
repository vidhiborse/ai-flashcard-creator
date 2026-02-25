"""
Test if PostgreSQL database connection works
"""
from dotenv import load_dotenv
import os

load_dotenv()

database_url = os.getenv("DATABASE_URL")

print("="*50)
print("DATABASE CONNECTION TEST")
print("="*50)

if not database_url:
    print("❌ ERROR: DATABASE_URL not found in .env file")
    print("Please add: DATABASE_URL=your_neon_connection_string")
    exit(1)

print(f"✅ Database URL found: {database_url[:30]}...")

# Fix postgres:// to postgresql://
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
    print("✅ Fixed database URL format")

# Test connection
try:
    import psycopg2
    from urllib.parse import urlparse
    
    result = urlparse(database_url)
    username = result.username
    password = result.password
    database = result.path[1:]
    hostname = result.hostname
    port = result.port or 5432
    
    print(f"✅ Connecting to: {hostname}")
    print(f"✅ Database: {database}")
    print(f"✅ User: {username}")
    
    connection = psycopg2.connect(
        database=database,
        user=username,
        password=password,
        host=hostname,
        port=port
    )
    
    print("✅ CONNECTION SUCCESSFUL!")
    print("✅ PostgreSQL database is working!")
    
    # Test query
    cursor = connection.cursor()
    cursor.execute("SELECT version();")
    version = cursor.fetchone()
    print(f"✅ PostgreSQL version: {version[0][:50]}...")
    
    cursor.close()
    connection.close()
    print("="*50)
    print("✅ ALL TESTS PASSED! Database is ready!")
    print("="*50)
    
except ImportError:
    print("❌ ERROR: psycopg2-binary not installed")
    print("Run: pip install psycopg2-binary")
    
except Exception as e:
    print("❌ CONNECTION FAILED!")
    print(f"Error: {e}")
    print("\nTroubleshooting:")
    print("1. Check your DATABASE_URL in .env")
    print("2. Make sure Neon project is active")
    print("3. Check your internet connection")