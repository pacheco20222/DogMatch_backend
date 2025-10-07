#!/usr/bin/env python3
"""
Run Flask-Migrate to create database tables on Azure MySQL
"""

import os
import sys
from flask_migrate import upgrade, init, migrate, current, revision

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app import create_app, db

def run_migrations():
    """Run database migrations"""
    print("🔄 Starting database migrations...")
    
    # Create Flask app
    app = create_app()
    
    with app.app_context():
        try:
            # Check current migration status
            print("📊 Checking current migration status...")
            
            # Run migrations
            print("⬆️  Running migrations...")
            upgrade()
            
            print("✅ Database migrations completed successfully!")
            
        except Exception as e:
            print(f"❌ Error during migrations: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    return True

if __name__ == '__main__':
    success = run_migrations()
    if success:
        print("🎉 All migrations completed successfully!")
        print("📋 Database tables should now be created on Azure MySQL")
    else:
        print("💥 Migration failed!")
        sys.exit(1)
