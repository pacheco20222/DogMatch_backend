#!/usr/bin/env python3
"""
Create admin user for DogMatch application
"""
from app import create_app, db
from app.models import User
from datetime import datetime

def create_admin_user():
    """Create admin user in the database"""
    
    print("=" * 60)
    print("Creating Admin User for DogMatch")
    print("=" * 60)
    
    app = create_app()
    
    with app.app_context():
        try:
            # Check if admin already exists
            existing_admin = User.query.filter_by(email='admin@dogmatch.com').first()
            if existing_admin:
                print("\n⚠️  Admin user already exists!")
                print(f"   Email: {existing_admin.email}")
                print(f"   Username: {existing_admin.username}")
                print(f"   User Type: {existing_admin.user_type}")
                return
            
            # Create admin user
            print("\n📝 Creating admin user...")
            admin = User(
                email='admin@dogmatch.com',
                password='Admin123!',
                username='admin',
                user_type='admin',
                first_name='Admin',
                last_name='DogMatch',
                phone='+1234567890',
                city='San Francisco',
                state='California',
                country='USA',
                is_active=True,
                is_verified=True
            )
            
            db.session.add(admin)
            db.session.commit()
            
            print("✅ Admin user created successfully!")
            print("\n" + "=" * 60)
            print("Admin User Credentials")
            print("=" * 60)
            print(f"Email:    admin@dogmatch.com")
            print(f"Password: Admin123!")
            print(f"Username: admin")
            print(f"Type:     admin")
            print("=" * 60)
            print("\n🎉 You can now login with these credentials!")
            print("   Use this account to create events and manage the app.")
            
        except Exception as e:
            print(f"\n❌ Error creating admin user!")
            print(f"Error: {str(e)}")
            db.session.rollback()

if __name__ == "__main__":
    create_admin_user()
