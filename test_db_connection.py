#!/usr/bin/env python3
"""
Test database connection to AWS MySQL instance
"""
import os
from dotenv import load_dotenv
import pymysql

# Load environment variables
load_dotenv()

def test_connection():
    """Test connection to AWS MySQL database"""
    
    # Get database credentials from environment
    db_host = os.getenv('DB_HOST')
    db_user = os.getenv('DB_USER')
    db_password = os.getenv('DB_PASSWORD')
    db_name = os.getenv('DB_NAME')
    db_port = int(os.getenv('DB_PORT', 3306))
    
    print("=" * 60)
    print("Testing AWS MySQL Database Connection")
    print("=" * 60)
    print(f"Host: {db_host}")
    print(f"Port: {db_port}")
    print(f"Database: {db_name}")
    print(f"User: {db_user}")
    print("-" * 60)
    
    try:
        # Attempt connection
        print("\n🔌 Attempting to connect to database...")
        connection = pymysql.connect(
            host=db_host,
            user=db_user,
            password=db_password,
            database=db_name,
            port=db_port,
            connect_timeout=10,
            ssl={'ssl_verify_cert': True, 'ssl_verify_identity': False}
        )
        
        print("✅ Connection successful!")
        
        # Test query
        print("\n📊 Testing database query...")
        with connection.cursor() as cursor:
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            print(f"✅ MySQL Version: {version[0]}")
            
            cursor.execute("SELECT DATABASE()")
            current_db = cursor.fetchone()
            print(f"✅ Current Database: {current_db[0]}")
            
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            print(f"\n📋 Existing Tables ({len(tables)}):")
            if tables:
                for table in tables:
                    print(f"   - {table[0]}")
            else:
                print("   (No tables found - database is empty)")
        
        connection.close()
        print("\n" + "=" * 60)
        print("✅ Database connection test PASSED")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n❌ Connection failed!")
        print(f"Error: {str(e)}")
        print("\n" + "=" * 60)
        print("❌ Database connection test FAILED")
        print("=" * 60)
        return False

if __name__ == "__main__":
    test_connection()
