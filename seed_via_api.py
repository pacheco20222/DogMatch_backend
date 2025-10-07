#!/usr/bin/env python3
"""
DogMatch Database Seeding Script via API
This script populates the database with sample data using the deployed backend API.
"""

import requests
import json
import random
from datetime import datetime, timedelta

# Configuration
BASE_URL = "https://dogmatch-backend.onrender.com"  # Your deployed backend URL
API_BASE = f"{BASE_URL}/api"

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

def make_request(method, endpoint, data=None, headers=None):
    """Make HTTP request to the API"""
    url = f"{API_BASE}{endpoint}"
    
    try:
        if method.upper() == 'GET':
            response = requests.get(url, headers=headers, timeout=30)
        elif method.upper() == 'POST':
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

def upload_dog_photo(token, dog_id, photo_data):
    """Upload a photo for a dog"""
    print(f"📸 Uploading photo for dog ID: {dog_id}")
    
    headers = {'Authorization': f'Bearer {token}'}
    
    # For now, we'll skip photo upload since we don't have actual image files
    # In a real scenario, you'd upload the paw.png image
    print(f"   ⏭️  Skipping photo upload (would upload paw.png)")
    return True

def create_event(token, event_data):
    """Create a new event"""
    print(f"🎉 Creating event: {event_data['title']}")
    
    headers = {'Authorization': f'Bearer {token}'}
    response = make_request('POST', '/events', event_data, headers)
    
    if response and response.status_code == 201:
        print(f"   ✅ Event {event_data['title']} created successfully")
        return response.json()
    else:
        print(f"   ❌ Failed to create event {event_data['title']}")
        if response:
            print(f"   Error: {response.text}")
        return None

def register_for_event(token, event_id, dog_id):
    """Register for an event"""
    print(f"🎟️  Registering for event ID: {event_id}")
    
    headers = {'Authorization': f'Bearer {token}'}
    registration_data = {
        'event_id': event_id,
        'dog_id': dog_id
    }
    
    response = make_request('POST', '/events/register', registration_data, headers)
    
    if response and response.status_code == 201:
        print(f"   ✅ Registered for event {event_id} successfully")
        return response.json()
    else:
        print(f"   ❌ Failed to register for event {event_id}")
        if response:
            print(f"   Error: {response.text}")
        return None

def swipe_dog(token, target_dog_id, action):
    """Swipe on a dog"""
    print(f"💕 Swiping {action} on dog ID: {target_dog_id}")
    
    headers = {'Authorization': f'Bearer {token}'}
    swipe_data = {
        'target_dog_id': target_dog_id,
        'action': action
    }
    
    response = make_request('POST', '/matches/swipe', swipe_data, headers)
    
    if response and response.status_code in [200, 201]:
        print(f"   ✅ Swiped {action} on dog {target_dog_id}")
        return response.json()
    else:
        print(f"   ❌ Failed to swipe on dog {target_dog_id}")
        if response:
            print(f"   Error: {response.text}")
        return None

def test_backend_connection():
    """Test if the backend is accessible"""
    print("🔍 Testing backend connection...")
    
    try:
        response = requests.get(BASE_URL, timeout=10)
        if response.status_code == 200:
            print("   ✅ Backend is accessible")
            return True
        else:
            print(f"   ⚠️  Backend responded with status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Backend connection failed: {e}")
        return False

def seed_database():
    """Main function to seed the database via API"""
    print("🌱 Starting DogMatch database seeding via API...")
    print(f"🎯 Using backend URL: {BASE_URL}")
    
    # Test backend connection first
    if not test_backend_connection():
        print("❌ Cannot proceed - backend is not accessible")
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
    
    # Step 2: Login users and create dogs
    print("\n🐕 Step 2: Creating dogs...")
    user_tokens = {}
    all_dogs = []
    
    for user_info in registered_users:
        user_data = user_info['data']
        token = login_user(user_data['email'], user_data['password'])
        
        if token:
            user_tokens[user_data['email']] = token
            
            # Create 1-3 dogs per user
            if user_data['user_type'] == 'owner':
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
                        all_dogs.append({
                            'dog_id': result.get('dog', {}).get('id'),
                            'owner_email': user_data['email']
                        })
                        
                        # Upload photo (skip for now)
                        upload_dog_photo(token, result.get('dog', {}).get('id'), {})
    
    print(f"✅ Created {len(all_dogs)} dogs")
    
    # Step 3: Create events (admin and shelter users)
    print("\n🎉 Step 3: Creating events...")
    events = []
    
    events_data = [
        {
            'title': 'Dog Park Meetup',
            'description': 'Join us for a fun day at the dog park! Bring your furry friends for some playtime and socialization.',
            'location': 'Central Park Dog Run',
            'event_date': (datetime.utcnow() + timedelta(days=7)).isoformat(),
            'max_participants': 20,
            'registration_fee': 0.00,
            'is_paid': False
        },
        {
            'title': 'Dog Training Workshop',
            'description': 'Learn basic obedience training techniques with certified trainers.',
            'location': 'Happy Tails Training Center',
            'event_date': (datetime.utcnow() + timedelta(days=14)).isoformat(),
            'max_participants': 15,
            'registration_fee': 25.00,
            'is_paid': True
        },
        {
            'title': 'Adoption Fair',
            'description': 'Meet adoptable dogs from local shelters. Find your new best friend!',
            'location': 'Community Center',
            'event_date': (datetime.utcnow() + timedelta(days=21)).isoformat(),
            'max_participants': 50,
            'registration_fee': 0.00,
            'is_paid': False
        }
    ]
    
    # Create events with admin and shelter users
    admin_emails = [u['data']['email'] for u in registered_users if u['data']['user_type'] in ['admin', 'shelter']]
    
    for event_data in events_data:
        if admin_emails:
            admin_email = random.choice(admin_emails)
            token = user_tokens.get(admin_email)
            
            if token:
                result = create_event(token, event_data)
                if result:
                    events.append({
                        'event_id': result.get('event', {}).get('id'),
                        'title': event_data['title']
                    })
    
    print(f"✅ Created {len(events)} events")
    
    # Step 4: Register for events
    print("\n🎟️  Step 4: Registering for events...")
    registrations = 0
    
    for event in events:
        # Register 3-5 random users for each event
        num_registrations = random.randint(3, 5)
        available_users = [u for u in registered_users if u['data']['user_type'] == 'owner']
        
        if available_users:
            selected_users = random.sample(available_users, min(num_registrations, len(available_users)))
            
            for user_info in selected_users:
                user_email = user_info['data']['email']
                token = user_tokens.get(user_email)
                
                if token:
                    # Get user's dogs
                    headers = {'Authorization': f'Bearer {token}'}
                    response = make_request('GET', '/dogs', headers=headers)
                    
                    if response and response.status_code == 200:
                        user_dogs = response.json().get('dogs', [])
                        if user_dogs:
                            dog_id = user_dogs[0]['id']  # Use first dog
                            result = register_for_event(token, event['event_id'], dog_id)
                            if result:
                                registrations += 1
    
    print(f"✅ Created {registrations} event registrations")
    
    # Step 5: Create some matches (swipes)
    print("\n💕 Step 5: Creating matches...")
    matches = 0
    
    # Get all dogs for swiping
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
                    result = swipe_dog(token, dog['id'], action)
                    if result:
                        matches += 1
    
    print(f"✅ Created {matches} swipes/matches")
    
    # Summary
    print("\n🎉 Database seeding completed successfully!")
    print(f"📊 Created:")
    print(f"   👥 {len(registered_users)} users")
    print(f"   🐕 {len(all_dogs)} dogs")
    print(f"   🎉 {len(events)} events")
    print(f"   🎟️  {registrations} event registrations")
    print(f"   💕 {matches} swipes/matches")
    
    print(f"\n🔑 Test credentials:")
    print(f"   📧 test@example.com / password123")
    print(f"   📧 admin@example.com / admin123")
    print(f"   📧 shelter@example.com / shelter123")

if __name__ == '__main__':
    try:
        seed_database()
    except Exception as e:
        print(f"❌ Error during seeding: {e}")
        import traceback
        traceback.print_exc()
