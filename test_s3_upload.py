#!/usr/bin/env python3
"""
Test S3 photo upload functionality
"""

import requests
import os

BASE_URL = "https://dogmatch-backend.onrender.com"
API_BASE = f"{BASE_URL}/api"

def test_s3_connection():
    """Test S3 connection"""
    print("🔍 Testing S3 connection...")
    
    # Login first
    login_data = {
        'email': 'test@example.com',
        'password': 'password123'
    }
    
    response = requests.post(f"{API_BASE}/auth/login", json=login_data)
    if response.status_code != 200:
        print(f"❌ Login failed: {response.text}")
        return None
    
    token = response.json().get('access_token')
    print(f"✅ Login successful")
    
    # Test S3 connection
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(f"{API_BASE}/s3/test-connection", headers=headers)
    
    if response.status_code == 200:
        print(f"✅ S3 connection successful: {response.json()}")
        return token
    else:
        print(f"❌ S3 connection failed: {response.text}")
        return None

def test_user_photo_upload(token):
    """Test user profile photo upload"""
    print("\n📸 Testing user profile photo upload...")
    
    # Find a sample photo
    sample_photos = []
    user_photos_dir = "sample_images/user_photos"
    if os.path.exists(user_photos_dir):
        sample_photos = [f for f in os.listdir(user_photos_dir) if f.endswith('.jpg')]
    
    if not sample_photos:
        print("❌ No sample photos found")
        return False
    
    photo_path = os.path.join(user_photos_dir, sample_photos[0])
    print(f"📁 Using photo: {photo_path}")
    
    headers = {'Authorization': f'Bearer {token}'}
    
    try:
        with open(photo_path, 'rb') as photo_file:
            files = {'photo': photo_file}
            response = requests.post(f"{API_BASE}/s3/upload/user-profile", headers=headers, files=files)
        
        print(f"📊 Response status: {response.status_code}")
        print(f"📊 Response text: {response.text}")
        
        if response.status_code == 200:
            print("✅ User profile photo upload successful")
            return True
        else:
            print("❌ User profile photo upload failed")
            return False
    except Exception as e:
        print(f"❌ Error uploading user photo: {e}")
        return False

def test_dog_photo_upload(token):
    """Test dog photo upload"""
    print("\n🐕 Testing dog photo upload...")
    
    # First, create a dog
    dog_data = {
        'name': 'Test Dog',
        'breed': 'Golden Retriever',
        'age': 3,
        'gender': 'male',
        'size': 'large',
        'description': 'A test dog for photo upload'
    }
    
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.post(f"{API_BASE}/dogs", json=dog_data, headers=headers)
    
    if response.status_code != 201:
        print(f"❌ Failed to create test dog: {response.text}")
        return False
    
    dog_result = response.json()
    print(f"✅ Test dog created: {dog_result}")
    
    # Try to get dog ID from response
    dog_id = None
    if 'dog' in dog_result:
        dog_id = dog_result['dog'].get('id')
    elif 'id' in dog_result:
        dog_id = dog_result['id']
    
    if not dog_id:
        print(f"❌ Could not extract dog ID from response: {dog_result}")
        return False
    
    print(f"🐕 Dog ID: {dog_id}")
    
    # Find a sample photo
    sample_photos = []
    dog_photos_dir = "sample_images/dog_photos"
    if os.path.exists(dog_photos_dir):
        sample_photos = [f for f in os.listdir(dog_photos_dir) if f.endswith('.jpg')]
    
    if not sample_photos:
        print("❌ No sample dog photos found")
        return False
    
    photo_path = os.path.join(dog_photos_dir, sample_photos[0])
    print(f"📁 Using photo: {photo_path}")
    
    try:
        with open(photo_path, 'rb') as photo_file:
            files = {'photo': photo_file}
            data = {'dog_id': str(dog_id)}
            response = requests.post(f"{API_BASE}/s3/upload/dog-photo", data=data, headers=headers, files=files)
        
        print(f"📊 Response status: {response.status_code}")
        print(f"📊 Response text: {response.text}")
        
        if response.status_code == 201:
            print("✅ Dog photo upload successful")
            return True
        else:
            print("❌ Dog photo upload failed")
            return False
    except Exception as e:
        print(f"❌ Error uploading dog photo: {e}")
        return False

if __name__ == '__main__':
    print("🧪 Testing S3 photo upload functionality...")
    
    # Test S3 connection
    token = test_s3_connection()
    if not token:
        print("❌ Cannot proceed without valid token")
        exit(1)
    
    # Test user photo upload
    test_user_photo_upload(token)
    
    # Test dog photo upload
    test_dog_photo_upload(token)
    
    print("\n🎯 Test completed!")
