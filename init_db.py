#!/usr/bin/env python3
"""
Initialize database with all tables from models
"""
from app import create_app, db

def init_database():
    """Create all database tables"""
    app = create_app()
    
    with app.app_context():
        # Drop all tables (if any exist)
        print("Dropping all existing tables...")
        db.drop_all()
        
        # Create all tables from models
        print("Creating all tables from models...")
        db.create_all()
        
        print("✅ Database initialized successfully!")
        print("\nTables created:")
        for table in db.metadata.sorted_tables:
            print(f"  - {table.name}")

if __name__ == "__main__":
    init_database()
