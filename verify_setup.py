import sys
import os

# Ensure we can import from the current directory
sys.path.append(os.getcwd())

from sqlalchemy import inspect
from database import engine, Base
from models import User

def check_database_schema():
    print("--- 🔍 Checking Database Schema ---")
    
    # Connect to the DB and get table info
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    # 1. Check if USERS table exists
    if "users" not in existing_tables:
        print("❌ ERROR: 'users' table missing.")
        print("   -> Run the main app once to generate the database file.")
        return False
        
    # 2. Check if ADMINS table is gone (optional, but good for cleanup)
    if "admins" in existing_tables:
        print("⚠️  WARNING: Old 'admins' table still exists. It is safe to ignore, but better to delete the .db file and regenerate.")

    # 3. Check for specific columns in USERS
    columns = [col['name'] for col in inspector.get_columns("users")]
    required_columns = ["hashed_password", "reset_count", "role"]
    
    missing = []
    for req in required_columns:
        if req not in columns:
            missing.append(req)
            
    if missing:
        print(f"❌ ERROR: The 'users' table exists but is missing these new columns: {missing}")
        print("   -> SOLUTION: Delete 'wekasafe.db' and restart the server.")
        return False
        
    print("✅ SUCCESS: 'users' table has the correct schema (including 'reset_count').")
    return True

if __name__ == "__main__":
    # Ensure tables are created if they don't exist yet
    Base.metadata.create_all(bind=engine)
    
    check_database_schema()