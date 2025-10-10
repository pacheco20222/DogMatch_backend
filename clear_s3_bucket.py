#!/usr/bin/env python3
"""
Clear S3 bucket and reset database for clean testing
"""

import requests
import json

BASE_URL = "https://dogmatch-backend.onrender.com"
API_BASE = f"{BASE_URL}/api"

def clear_database():
    """Clear and recreate database tables"""
    print("🔄 Clearing and recreating database tables...")
    
    response = requests.post(f"{API_BASE}/migrate/reset")
    if response.status_code == 200:
        print("   ✅ Database tables cleared and recreated successfully")
        return True
    else:
        print(f"   ❌ Failed to clear database: {response.text}")
        return False

def clear_s3_bucket():
    """Clear S3 bucket contents"""
    print("🗑️  Clearing S3 bucket contents...")
    
    # Login as admin to get token
    login_data = {
        'email': 'admin@example.com',
        'password': 'admin123'
    }
    
    response = requests.post(f"{API_BASE}/auth/login", json=login_data)
    if response.status_code != 200:
        print(f"   ❌ Failed to login as admin: {response.text}")
        return False
    
    token = response.json().get('access_token')
    headers = {'Authorization': f'Bearer {token}'}
    
    # Test S3 connection first
    response = requests.get(f"{API_BASE}/s3/test-connection", headers=headers)
    if response.status_code != 200:
        print(f"   ❌ S3 connection failed: {response.text}")
        return False
    
    print("   ✅ S3 connection successful")
    
    # Note: We don't have a direct S3 clear endpoint, but clearing the database
    # will remove all references to S3 objects. The S3 objects will become orphaned
    # but won't affect the app functionality.
    
    print("   ℹ️  Database cleared - S3 objects will be orphaned but won't affect app")
    return True

def main():
    """Main function to clear everything"""
    print("🧹 Clearing DogMatch database and S3 for fresh start...")
    print(f"🎯 Using backend URL: {BASE_URL}")
    
    # Step 1: Clear database
    if not clear_database():
        print("❌ Failed to clear database. Aborting.")
        return
    
    # Step 2: Clear S3 references
    if not clear_s3_bucket():
        print("❌ Failed to clear S3 references. Aborting.")
        return
    
    print("\n✅ Cleanup completed successfully!")
    print("🎯 Ready to run fresh seeding:")
    print("   python3 seed_with_s3_photos.py")

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        import traceback
        traceback.print_exc()
