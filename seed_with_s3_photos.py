#!/usr/bin/env python3
"""
DogMatch Database Seeding Script with S3 Photo Uploads
This script populates the database with sample data and uploads real photos to S3.
"""

import requests
import json
import random
import time
import os
from datetime import datetime, timedelta

# Configuration
BASE_URL = "https://dogmatch-backend.onrender.com"
API_BASE = f"{BASE_URL}/api"

# Sample images directory
SAMPLE_IMAGES_DIR = "sample_images"

# Generate unique timestamp for this seeding session
TIMESTAMP = int(time.time())

# Sample data
USERS_DATA = [
    {
        'email': 'test@example.com',
        'password': 'password123',
        'username': 'testuser',
        'first_name': 'Test',
        'last_name': 'User',
        'user_type': 'owner',
        'phone': '+1234567890'
    },
    {
        'email': 'admin@example.com',
        'password': 'admin123',
        'username': 'adminuser',
        'first_name': 'Admin',
        'last_name': 'User',
        'user_type': 'admin',
        'phone': '+1234567891'
    },
    {
        'email': 'shelter@example.com',
        'password': 'shelter123',
        'username': 'happyshelter',
        'first_name': 'Happy',
        'last_name': 'Shelter',
        'user_type': 'shelter',
        'phone': '+1234567892'
    },
    {
        'email': 'john@example.com',
        'password': 'password123',
        'username': 'johnsmith',
        'first_name': 'John',
        'last_name': 'Smith',
        'user_type': 'owner',
        'phone': '+1234567893'
    },
    {
        'email': 'sarah@example.com',
        'password': 'password123',
        'username': 'sarahjohnson',
        'first_name': 'Sarah',
        'last_name': 'Johnson',
        'user_type': 'owner',
        'phone': '+1234567894'
    },
    {
        'email': 'mike@example.com',
        'password': 'password123',
        'username': 'mikewilson',
        'first_name': 'Mike',
        'last_name': 'Wilson',
        'user_type': 'owner',
        'phone': '+1234567895'
    },
    {
        'email': 'emma@example.com',
        'password': 'password123',
        'username': 'emmabrown',
        'first_name': 'Emma',
        'last_name': 'Brown',
        'user_type': 'owner',
        'phone': '+1234567896'
    },
    {
        'email': 'david@example.com',
        'password': 'password123',
        'username': 'daviddavis',
        'first_name': 'David',
        'last_name': 'Davis',
        'user_type': 'owner',
        'phone': '+1234567897'
    },
    {
        'email': 'lisa@example.com',
        'password': 'password123',
        'username': 'lisamiller',
        'first_name': 'Lisa',
        'last_name': 'Miller',
        'user_type': 'owner',
        'phone': '+1234567898'
    },
    {
        'email': 'chris@example.com',
        'password': 'password123',
        'username': 'chrisgarcia',
        'first_name': 'Chris',
        'last_name': 'Garcia',
        'user_type': 'owner',
        'phone': '+1234567899'
    },
    {
        'email': 'shelter2@example.com',
        'password': 'shelter123',
        'username': 'pawsrescue',
        'first_name': 'Paws',
        'last_name': 'Rescue',
        'user_type': 'shelter',
        'phone': '+1234567800'
    }
]

DOG_BREEDS = [
    'Golden Retriever', 'Labrador Retriever', 'German Shepherd', 'French Bulldog',
    'Bulldog', 'Poodle', 'Beagle', 'Rottweiler', 'German Shorthaired Pointer',
    'Yorkshire Terrier', 'Siberian Husky', 'Dachshund', 'Boxer', 'Great Dane',
    'Chihuahua', 'Shih Tzu', 'Boston Terrier', 'Border Collie', 'Australian Shepherd',
    'Cocker Spaniel', 'Maltese', 'Jack Russell Terrier', 'Pomeranian', 'Mastiff'
]

DOG_NAMES = [
    'Buddy', 'Bella', 'Max', 'Luna', 'Charlie', 'Lucy', 'Cooper', 'Daisy',
    'Rocky', 'Molly', 'Duke', 'Sadie', 'Bear', 'Maggie', 'Tucker', 'Sophie',
    'Zeus', 'Chloe', 'Jack', 'Lola', 'Toby', 'Zoe', 'Oscar', 'Ruby',
    'Milo', 'Penny', 'Finn', 'Gracie', 'Bentley', 'Lily', 'Murphy', 'Stella',
    'Rex', 'Nala', 'Jake', 'Coco', 'Bruno', 'Rosie', 'Gus', 'Mia'
]

def make_request(method, endpoint, data=None, headers=None, files=None):
    """Make HTTP request to the API"""
    url = f"{API_BASE}{endpoint}"
    
    try:
        if method.upper() == 'GET':
            response = requests.get(url, headers=headers, timeout=30)
        elif method.upper() == 'POST':
            # Use form data when files are present, JSON otherwise
            if files:
                response = requests.post(url, data=data, headers=headers, files=files, timeout=30)
            else:
                response = requests.post(url, json=data, headers=headers, timeout=30)
        elif method.upper() == 'PUT':
            response = requests.put(url, json=data, headers=headers, timeout=30)
        elif method.upper() == 'DELETE':
            response = requests.delete(url, headers=headers, timeout=30)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        return response
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None

def register_user(user_data):
    """Register a new user"""
    print(f"👤 Registering user: {user_data['email']}")
    
    response = make_request('POST', '/auth/register', user_data)
    
    if response and response.status_code == 201:
        print(f"   ✅ User {user_data['email']} registered successfully")
        return response.json()
    else:
        print(f"   ❌ Failed to register user {user_data['email']}")
        if response:
            print(f"   Status Code: {response.status_code}")
            print(f"   Error: {response.text}")
        else:
            print(f"   No response received")
        return None

def login_user(email, password):
    """Login user and get access token"""
    print(f"🔐 Logging in user: {email}")
    
    login_data = {
        'email': email,
        'password': password
    }
    
    response = make_request('POST', '/auth/login', login_data)
    
    if response and response.status_code == 200:
        data = response.json()
        token = data.get('access_token')
        print(f"   ✅ User {email} logged in successfully")
        return token
    else:
        print(f"   ❌ Failed to login user {email}")
        if response:
            print(f"   Error: {response.text}")
        return None

def upload_user_profile_photo(token, user_id, photo_path):
    """Upload user profile photo to S3"""
    print(f"📸 Uploading profile photo for user {user_id}")
    
    if not os.path.exists(photo_path):
        print(f"   ⚠️  Photo file not found: {photo_path}")
        return False
    
    headers = {'Authorization': f'Bearer {token}'}
    
    try:
        with open(photo_path, 'rb') as photo_file:
            files = {'photo': photo_file}
            response = make_request('POST', '/s3/upload/user-profile', headers=headers, files=files)
        
        if response and response.status_code == 200:
            print(f"   ✅ Profile photo uploaded for user {user_id}")
            return True
        else:
            print(f"   ❌ Failed to upload profile photo for user {user_id}")
            if response:
                print(f"   Error: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Error uploading profile photo: {e}")
        return False

def create_dog(token, dog_data):
    """Create a new dog"""
    print(f"🐕 Creating dog: {dog_data['name']}")
    
    headers = {'Authorization': f'Bearer {token}'}
    response = make_request('POST', '/dogs', dog_data, headers)
    
    if response and response.status_code == 201:
        print(f"   ✅ Dog {dog_data['name']} created successfully")
        return response.json()
    else:
        print(f"   ❌ Failed to create dog {dog_data['name']}")
        if response:
            print(f"   Error: {response.text}")
        return None

def upload_dog_photo(token, dog_id, photo_path):
    """Upload dog photo to S3"""
    print(f"📸 Uploading photo for dog {dog_id}")
    
    if not os.path.exists(photo_path):
        print(f"   ⚠️  Photo file not found: {photo_path}")
        return False
    
    headers = {'Authorization': f'Bearer {token}'}
    
    try:
        with open(photo_path, 'rb') as photo_file:
            files = {'photo': photo_file}
            data = {'dog_id': str(dog_id)}  # Convert to string for form data
            response = make_request('POST', '/s3/upload/dog-photo', data=data, headers=headers, files=files)
        
        if response and response.status_code == 201:
            print(f"   ✅ Photo uploaded for dog {dog_id}")
            return True
        else:
            print(f"   ❌ Failed to upload photo for dog {dog_id}")
            if response:
                print(f"   Error: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Error uploading dog photo: {e}")
        return False

def get_sample_photos(photo_type, count):
    """Get list of sample photo files"""
    photo_dir = os.path.join(SAMPLE_IMAGES_DIR, photo_type)
    if not os.path.exists(photo_dir):
        print(f"   ⚠️  Photo directory not found: {photo_dir}")
        return []
    
    photos = [f for f in os.listdir(photo_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))]
    photos.sort()  # Sort for consistent ordering
    print(f"   📁 Found {len(photos)} {photo_type}: {photos}")
    return photos[:count]

def test_s3_connection(token):
    """Test S3 connection"""
    print("🔍 Testing S3 connection...")
    
    headers = {'Authorization': f'Bearer {token}'}
    response = make_request('GET', '/s3/test-connection', headers=headers)
    
    if response and response.status_code == 200:
        print("   ✅ S3 connection successful")
        return True
    else:
        print("   ❌ S3 connection failed")
        if response:
            print(f"   Error: {response.text}")
        return False

def seed_database_with_photos():
    """Main function to seed the database with S3 photos"""
    print("🌱 Starting DogMatch database seeding with S3 photos...")
    print(f"🎯 Using backend URL: {BASE_URL}")
    
    # Step 0: Clear and recreate database tables
    print("\n🔄 Step 0: Clearing and recreating database tables...")
    reset_response = make_request('POST', '/migrate/reset')
    if reset_response and reset_response.status_code == 200:
        print("   ✅ Database tables cleared and recreated successfully")
    else:
        print("   ❌ Failed to clear/recreate database tables. Aborting seeding.")
        if reset_response:
            print(f"   Status Code: {reset_response.status_code}")
            print(f"   Error: {reset_response.text}")
        return
    
    # Step 1: Register all users
    print("\n📝 Step 1: Registering users...")
    registered_users = []
    
    for user_data in USERS_DATA:
        result = register_user(user_data)
        if result:
            registered_users.append({
                'data': user_data,
                'user_id': result.get('user', {}).get('id')
            })
    
    print(f"✅ Registered {len(registered_users)} users")
    
    # Step 2: Login users and upload profile photos
    print("\n📸 Step 2: Uploading user profile photos...")
    user_tokens = {}
    user_photos = get_sample_photos('user_photos', 50)  # Get all available photos
    used_user_photos = set()  # Track which user photos have been used
    
    for i, user_info in enumerate(registered_users):
        user_data = user_info['data']
        token = login_user(user_data['email'], user_data['password'])
        
        if token:
            user_tokens[user_data['email']] = token
            
            # Test S3 connection on first user
            if i == 0:
                if not test_s3_connection(token):
                    print("❌ S3 connection failed. Please check AWS credentials.")
                    return
            
            # Find an unused user photo
            available_user_photos = [p for p in user_photos if p not in used_user_photos]
            if available_user_photos:
                selected_photo = available_user_photos[0]
                used_user_photos.add(selected_photo)
                photo_path = os.path.join(SAMPLE_IMAGES_DIR, 'user_photos', selected_photo)
                print(f"   📸 Using user photo: {selected_photo}")
                upload_user_profile_photo(token, user_info['user_id'], photo_path)
            else:
                print(f"   ⚠️  No more user photos available for user {user_info['user_id']}")
    
    # Step 3: Create dogs and upload photos
    print("\n🐕 Step 3: Creating dogs with photos...")
    all_dogs = []
    dog_photos = get_sample_photos('dog_photos', 50)  # Get all available photos
    used_photos = set()  # Track which photos have been used
    
    for user_info in registered_users:
        user_data = user_info['data']
        token = user_tokens.get(user_data['email'])
        
        if token and user_data['user_type'] == 'owner':
            # Create 1-3 dogs per user
            num_dogs = random.randint(1, 3)
            
            for i in range(num_dogs):
                dog_data = {
                    'name': random.choice(DOG_NAMES),
                    'breed': random.choice(DOG_BREEDS),
                    'age': random.randint(1, 12),
                    'gender': random.choice(['male', 'female']),
                    'size': random.choice(['small', 'medium', 'large']),
                    'description': f"A friendly and energetic {random.choice(DOG_BREEDS).lower()} who loves to play and make new friends!"
                }
                
                result = create_dog(token, dog_data)
                if result:
                    # Try different possible response structures
                    dog_id = (result.get('Dog', {}).get('id') or 
                             result.get('dog', {}).get('id') or 
                             result.get('id') or 
                             result.get('dog_id'))
                    if dog_id:
                        all_dogs.append({
                            'dog_id': dog_id,
                            'owner_email': user_data['email']
                        })
                        
                        # Find an unused photo
                        available_photos = [p for p in dog_photos if p not in used_photos]
                        if available_photos:
                            selected_photo = available_photos[0]
                            used_photos.add(selected_photo)
                            photo_path = os.path.join(SAMPLE_IMAGES_DIR, 'dog_photos', selected_photo)
                            print(f"   📸 Using photo: {selected_photo}")
                            upload_dog_photo(token, dog_id, photo_path)
                        else:
                            print(f"   ⚠️  No more photos available for dog {dog_id}")
    
    print(f"✅ Created {len(all_dogs)} dogs with photos")
    
    # Step 4: Create some initial swipes
    print("\n💕 Step 4: Creating initial swipes...")
    matches = 0
    
    if all_dogs:
        # Use the first user to swipe on other dogs
        first_user_email = registered_users[0]['data']['email']
        token = user_tokens.get(first_user_email)
        
        if token:
            # Get discoverable dogs
            headers = {'Authorization': f'Bearer {token}'}
            response = make_request('GET', '/dogs/discover', headers=headers)
            
            if response and response.status_code == 200:
                discoverable_dogs = response.json().get('dogs', [])
                
                # Swipe on first few dogs
                for i, dog in enumerate(discoverable_dogs[:5]):
                    action = random.choice(['like', 'pass', 'super_like'])
                    
                    swipe_data = {
                        'target_dog_id': dog['id'],
                        'action': action
                    }
                    
                    swipe_response = make_request('POST', '/matches/swipe', swipe_data, headers)
                    if swipe_response and swipe_response.status_code in [200, 201]:
                        matches += 1
    
    print(f"✅ Created {matches} swipes/matches")
    
    # Summary
    print("\n🎉 Database seeding with S3 photos completed successfully!")
    print(f"📊 Created:")
    print(f"   👥 {len(registered_users)} users with profile photos")
    print(f"   🐕 {len(all_dogs)} dogs with photos")
    print(f"   💕 {matches} swipes/matches")
    
    print(f"\n🔑 Test credentials:")
    print(f"   📧 test@example.com / password123")
    print(f"   📧 admin@example.com / admin123")
    print(f"   📧 shelter@example.com / shelter123")
    
    print(f"\n📁 Sample photos used from: {SAMPLE_IMAGES_DIR}/")
    print(f"   👤 User photos: {len(user_photos)} files")
    print(f"   🐕 Dog photos: {len(dog_photos)} files")

if __name__ == '__main__':
    try:
        seed_database_with_photos()
    except Exception as e:
        print(f"❌ Error during seeding: {e}")
        import traceback
        traceback.print_exc()
