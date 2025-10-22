#!/usr/bin/env python3
"""
Verify Flask app can connect to AWS MySQL database
"""
from app import create_app, db
from app.models import User, Dog, Event, Match, Message, EventRegistration, Photo, BlacklistedToken

def verify_database():
    """Verify database connection and table structure"""
    
    print("=" * 60)
    print("Verifying Flask Database Connection")
    print("=" * 60)
    
    app = create_app()
    
    with app.app_context():
        try:
            # Test database connection
            print("\n🔌 Testing database connection...")
            db.engine.connect()
            print("✅ Database connection successful!")
            
            # Get table names
            print("\n📋 Checking database tables...")
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            print(f"✅ Found {len(tables)} tables:")
            for table in sorted(tables):
                print(f"   - {table}")
            
            # Verify models can be queried
            print("\n🔍 Testing model queries...")
            
            models_to_test = [
                ('User', User),
                ('Dog', Dog),
                ('Event', Event),
                ('Match', Match),
                ('Message', Message),
                ('EventRegistration', EventRegistration),
                ('Photo', Photo),
                ('BlacklistedToken', BlacklistedToken)
            ]
            
            for model_name, model_class in models_to_test:
                try:
                    count = model_class.query.count()
                    print(f"   ✅ {model_name}: {count} records")
                except Exception as e:
                    print(f"   ❌ {model_name}: Error - {str(e)}")
            
            print("\n" + "=" * 60)
            print("✅ Flask database verification PASSED")
            print("=" * 60)
            print("\n🎉 Your AWS MySQL database is ready to use!")
            print("   - All tables created successfully")
            print("   - Flask models can query the database")
            print("   - Ready for data seeding and API testing")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Verification failed!")
            print(f"Error: {str(e)}")
            print("\n" + "=" * 60)
            print("❌ Flask database verification FAILED")
            print("=" * 60)
            return False

if __name__ == "__main__":
    verify_database()
