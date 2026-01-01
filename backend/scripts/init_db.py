#!/usr/bin/env python3
"""
Initialize database with default data
Run this script from the backend/ directory:
    python scripts/init_db.py
"""
import sys
import os

# Add backend directory to path (assumes script is run from backend/)
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from core.database.connection import init_database, get_db_manager
from core.database.models import User, UserRole
from auth.authenticator import get_password_hash
from config.settings import get_settings


def init_default_admin():
    """Create default admin user if it doesn't exist"""
    settings = get_settings()
    db_manager = get_db_manager()
    
    # Get session from generator properly - Session is NOT a context manager
    session_gen = db_manager.get_session()
    db = next(session_gen)
    
    try:
        # Check if admin user exists
        admin = db.query(User).filter(User.username == "admin").first()
        if admin:
            print("Admin user already exists")
            return
        
        # Create admin user
        admin_password = os.getenv("ADMIN_PASSWORD", "admin")
        admin_user = User(
            username="admin",
            email="admin@example.com",
            password_hash=get_password_hash(admin_password),
            role=UserRole.ADMINISTRATOR,
            is_active=True
        )
        db.add(admin_user)
        db.commit()
        print(f"Created admin user with password: {admin_password}")
        print("Please change the password after first login!")
    except Exception as e:
        db.rollback()
        print(f"Error creating admin user: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    settings = get_settings()
    print(f"Initializing database at: {settings.db_path}")
    
    try:
    init_database(settings.db_path, settings.db_password or "")
    init_default_admin()
    print("Database initialized successfully!")
    except Exception as e:
        print(f"Error initializing database: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

