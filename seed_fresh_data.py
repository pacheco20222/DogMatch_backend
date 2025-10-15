#!/usr/bin/env python3
"""
Create fresh seed data for the DogMatch application.
This script will create users, dogs, matches, and messages for testing.
"""

import os
import sys
import random
from datetime import datetime, timedelta

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User, Dog, Match, Message, Event, EventRegistration
from app.services.s3_service import s3_service

# Sample data
DOG_NAMES = [
    "Buddy", "Bella", "Max", "Luna", "Charlie", "Lucy", "Cooper", "Daisy",
    "Rocky", "Molly", "Duke", "Sadie", "Bear", "Maggie", "Tucker", "Sophie",
    "Zeus", "Chloe", "Jack", "Lola", "Toby", "Zoe", "Oscar", "Ruby",
    "Milo", "Penny", "Finn", "Nala", "Leo", "Stella", "Bentley", "Willow"
]

DOG_BREEDS = [
    "Golden Retriever", "Labrador Retriever", "German Shepherd", "French Bulldog",
    "Bulldog", "Poodle", "Beagle", "Rottweiler", "German Shorthaired Pointer",
    "Yorkshire Terrier", "Siberian Husky", "Dachshund", "Boxer", "Great Dane",
    "Chihuahua", "Shih Tzu", "Boston Terrier", "Border Collie", "Australian Shepherd",
    "Cocker Spaniel", "Maltese", "Pomeranian", "Jack Russell Terrier", "Dalmatian"
]

DOG_SIZES = ["Small", "Medium", "Large", "Extra Large"]
DOG_ENERGY_LEVELS = ["Low", "Medium", "High"]
DOG_PERSONALITIES = [
    ["Friendly", "Playful", "Energetic"],
    ["Calm", "Gentle", "Loyal"],
    ["Adventurous", "Independent", "Smart"],
    ["Affectionate", "Social", "Curious"],
    ["Protective", "Confident", "Active"],
    ["Sweet", "Patient", "Easygoing"]
]

USER_FIRST_NAMES = [
    "Alex", "Jordan", "Taylor", "Casey", "Morgan", "Riley", "Avery", "Quinn",
    "Blake", "Cameron", "Drew", "Emery", "Finley", "Hayden", "Jamie", "Kendall",
    "Logan", "Parker", "Reese", "Sage", "Skyler", "Tatum", "River", "Phoenix"
]

USER_LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas",
    "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson", "White"
]

DOG_DESCRIPTIONS = [
    "A loving and energetic companion who loves to play fetch and go on long walks.",
    "Gentle and calm, perfect for families with children. Loves cuddles and treats.",
    "Adventurous spirit who enjoys hiking and outdoor activities. Very social with other dogs.",
    "Smart and loyal, great with training. Loves to learn new tricks and commands.",
    "Sweet and affectionate, always ready for belly rubs and playtime.",
    "Active and playful, needs plenty of exercise and mental stimulation.",
    "Friendly and outgoing, gets along well with everyone including other pets.",
    "Calm and patient, perfect for first-time dog owners. Very well-behaved."
]

MESSAGE_TEMPLATES = [
    "Hey! Your dog looks amazing! 🐕",
    "Hi there! Would love to set up a playdate!",
    "Your pup is so cute! What's their favorite activity?",
    "Hello! I think our dogs would get along great!",
    "Hi! My dog loves meeting new friends. Want to meet up?",
    "Your dog is adorable! How old are they?",
    "Hey! I'd love to chat more about our dogs!",
    "Hi there! Your dog looks like they have so much energy!",
    "Hello! What's your dog's favorite treat?",
    "Hi! I think our dogs would be great playmates!",
    "Your dog is so photogenic! 📸",
    "Hey! Want to go for a walk together sometime?",
    "Hi! Your dog looks so happy and healthy!",
    "Hello! I love your dog's breed!",
    "Hi there! Your pup seems very well-trained!",
    "Hey! What's your dog's favorite toy?",
    "Hi! I think our dogs have similar personalities!",
    "Hello! Your dog looks like they love adventures!",
    "Hi there! Would love to know more about your dog!",
    "Hey! Your dog is absolutely beautiful! ✨"
]

def get_random_s3_photo(folder, count):
    """Get a random S3 photo URL from the specified folder"""
    try:
        # List objects in the S3 folder
        objects = s3_service.list_objects(folder)
        if objects:
            # Return a random photo URL
            random_photo = random.choice(objects)
            return f"https://dogmatch-bucket.s3.amazonaws.com/{random_photo}"
        else:
            # Fallback to a default image
            return "https://images.unsplash.com/photo-1552053831-71594a27632d?w=400&h=600&fit=crop&crop=face"
    except Exception as e:
        print(f"Warning: Could not get S3 photo from {folder}: {str(e)}")
        return "https://images.unsplash.com/photo-1552053831-71594a27632d?w=400&h=600&fit=crop&crop=face"

def create_users():
    """Create sample users"""
    print("👤 Creating users...")
    users = []
    
    # Create admin user
    admin = User(
        email="admin@dogmatch.com",
        username="admin",
        first_name="Admin",
        last_name="User",
        password_hash=User.hash_password("admin123"),
        role="admin",
        is_verified=True,
        profile_photo_url=get_random_s3_photo("user-photos", 1)
    )
    users.append(admin)
    
    # Create shelter user
    shelter = User(
        email="shelter@dogmatch.com",
        username="happy_paws_shelter",
        first_name="Happy",
        last_name="Paws",
        password_hash=User.hash_password("shelter123"),
        role="shelter",
        is_verified=True,
        profile_photo_url=get_random_s3_photo("user-photos", 1)
    )
    users.append(shelter)
    
    # Create regular users (dog owners)
    for i in range(12):
        first_name = random.choice(USER_FIRST_NAMES)
        last_name = random.choice(USER_LAST_NAMES)
        username = f"{first_name.lower()}_{last_name.lower()}_{i+1}"
        email = f"{username}@example.com"
        
        user = User(
            email=email,
            username=username,
            first_name=first_name,
            last_name=last_name,
            password_hash=User.hash_password("password123"),
            role="owner",
            is_verified=True,
            profile_photo_url=get_random_s3_photo("user-photos", 1)
        )
        users.append(user)
    
    # Add all users to database
    for user in users:
        db.session.add(user)
    
    db.session.commit()
    print(f"✅ Created {len(users)} users")
    return users

def create_dogs(users):
    """Create sample dogs for users"""
    print("🐕 Creating dogs...")
    dogs = []
    
    # Get owner users (exclude admin and shelter)
    owner_users = [user for user in users if user.role == "owner"]
    
    for user in owner_users:
        # Each owner has 1-2 dogs
        num_dogs = random.randint(1, 2)
        
        for i in range(num_dogs):
            name = random.choice(DOG_NAMES)
            breed = random.choice(DOG_BREEDS)
            size = random.choice(DOG_SIZES)
            energy_level = random.choice(DOG_ENERGY_LEVELS)
            personality = random.choice(DOG_PERSONALITIES)
            description = random.choice(DOG_DESCRIPTIONS)
            
            dog = Dog(
                owner_id=user.id,
                name=name,
                age=random.randint(1, 12),
                breed=breed,
                size=size,
                energy_level=energy_level,
                description=description,
                is_available=True,
                is_adopted=False,
                profile_photo_url=get_random_s3_photo("dog-photos", 1)
            )
            
            # Set personality traits
            dog.set_personality_list(personality)
            
            dogs.append(dog)
            db.session.add(dog)
    
    db.session.commit()
    print(f"✅ Created {len(dogs)} dogs")
    return dogs

def create_matches_and_messages(dogs):
    """Create matches and messages between dogs"""
    print("💕 Creating matches and messages...")
    
    # Create some mutual matches (both dogs liked each other)
    mutual_matches = []
    for i in range(6):
        dog1 = random.choice(dogs)
        dog2 = random.choice([d for d in dogs if d.id != dog1.id and d.owner_id != dog1.owner_id])
        
        # Create mutual match
        match = Match(
            dog_one_id=dog1.id,
            dog_two_id=dog2.id,
            dog_one_action='like',
            dog_two_action='like',
            status='matched'
        )
        mutual_matches.append(match)
        db.session.add(match)
    
    # Create some pending swipes (only one dog has swiped)
    for i in range(4):
        dog1 = random.choice(dogs)
        dog2 = random.choice([d for d in dogs if d.id != dog1.id and d.owner_id != dog1.owner_id])
        
        # Create pending match
        match = Match(
            dog_one_id=dog1.id,
            dog_two_id=dog2.id,
            dog_one_action='like',
            dog_two_action='pending',
            status='pending'
        )
        db.session.add(match)
    
    # Create some one-sided swipes (for current user to see in discover)
    for i in range(3):
        dog1 = random.choice(dogs)
        dog2 = random.choice([d for d in dogs if d.id != dog1.id and d.owner_id != dog1.owner_id])
        
        # Create one-sided match
        match = Match(
            dog_one_id=dog1.id,
            dog_two_id=dog2.id,
            dog_one_action='pass',
            dog_two_action='pending',
            status='pending'
        )
        db.session.add(match)
    
    db.session.commit()
    
    # Create messages for mutual matches
    print("💬 Creating messages...")
    messages_created = 0
    
    for match in mutual_matches:
        # Get the two dogs and their owners
        dog1 = next(d for d in dogs if d.id == match.dog_one_id)
        dog2 = next(d for d in dogs if d.id == match.dog_two_id)
        owner1 = dog1.owner
        owner2 = dog2.owner
        
        # Create 3-8 messages between the owners
        num_messages = random.randint(3, 8)
        
        for i in range(num_messages):
            # Alternate between the two owners
            sender = owner1 if i % 2 == 0 else owner2
            content = random.choice(MESSAGE_TEMPLATES)
            
            # Create message with some time variation
            sent_at = datetime.utcnow() - timedelta(
                days=random.randint(0, 7),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
            
            message = Message(
                match_id=match.id,
                sender_user_id=sender.id,
                content=content,
                message_type='text',
                sent_at=sent_at
            )
            
            db.session.add(message)
            messages_created += 1
    
    db.session.commit()
    print(f"✅ Created {len(mutual_matches)} mutual matches and {messages_created} messages")

def create_events(users):
    """Create sample events"""
    print("🎉 Creating events...")
    
    # Get shelter user
    shelter_user = next((user for user in users if user.role == "shelter"), None)
    if not shelter_user:
        print("⚠️  No shelter user found, skipping events")
        return
    
    events_data = [
        {
            "title": "Dog Park Meetup",
            "description": "Join us for a fun day at the local dog park! Bring your furry friends for some playtime and socialization.",
            "location": "Central Dog Park",
            "event_date": datetime.utcnow() + timedelta(days=7),
            "max_attendees": 20
        },
        {
            "title": "Puppy Training Workshop",
            "description": "Learn basic training techniques for your new puppy. Perfect for first-time dog owners!",
            "location": "Happy Paws Training Center",
            "event_date": datetime.utcnow() + timedelta(days=14),
            "max_attendees": 15
        },
        {
            "title": "Dog Adoption Fair",
            "description": "Meet adorable dogs looking for their forever homes. Adoption fees waived for this special event!",
            "location": "Community Center",
            "event_date": datetime.utcnow() + timedelta(days=21),
            "max_attendees": 50
        }
    ]
    
    events = []
    for event_data in events_data:
        event = Event(
            title=event_data["title"],
            description=event_data["description"],
            location=event_data["location"],
            event_date=event_data["event_date"],
            max_attendees=event_data["max_attendees"],
            created_by=shelter_user.id,
            image_url=get_random_s3_photo("event-photos", 1)
        )
        events.append(event)
        db.session.add(event)
    
    db.session.commit()
    print(f"✅ Created {len(events)} events")

def seed_database():
    """Main function to seed the database"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🌱 Starting database seeding...")
            print(f"📊 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Create users
            users = create_users()
            
            # Create dogs
            dogs = create_dogs(users)
            
            # Create matches and messages
            create_matches_and_messages(dogs)
            
            # Create events
            create_events(users)
            
            print("✅ Database seeding completed successfully!")
            print(f"📊 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Print summary
            print("\n📈 Summary:")
            print(f"  👤 Users: {User.query.count()}")
            print(f"  🐕 Dogs: {Dog.query.count()}")
            print(f"  💕 Matches: {Match.query.count()}")
            print(f"  💬 Messages: {Message.query.count()}")
            print(f"  🎉 Events: {Event.query.count()}")
            
        except Exception as e:
            print(f"❌ Error seeding database: {str(e)}")
            db.session.rollback()
            raise

if __name__ == "__main__":
    seed_database()
