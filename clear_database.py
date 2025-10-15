#!/usr/bin/env python3
"""
Clear all existing data from the database while keeping the structure intact.
This script will delete all records from all tables but preserve the schema.
"""

import os
import sys
from datetime import datetime

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User, Dog, Match, Message, Event, EventRegistration

def clear_database():
    """Clear all data from the database"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🗑️  Starting database cleanup...")
            
            # Delete in reverse order of dependencies to avoid foreign key constraints
            print("📧 Deleting messages...")
            Message.query.delete()
            
            print("💕 Deleting matches...")
            Match.query.delete()
            
            print("📅 Deleting event registrations...")
            EventRegistration.query.delete()
            
            print("🎉 Deleting events...")
            Event.query.delete()
            
            print("🐕 Deleting dogs...")
            Dog.query.delete()
            
            print("👤 Deleting users...")
            User.query.delete()
            
            # Commit all deletions
            db.session.commit()
            
            print("✅ Database cleared successfully!")
            print(f"📊 Cleared at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
        except Exception as e:
            print(f"❌ Error clearing database: {str(e)}")
            db.session.rollback()
            raise

if __name__ == "__main__":
    clear_database()
