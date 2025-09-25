#!/usr/bin/env python3
"""
Comprehensive Database Seeding Script for DogMatch Backend
Creates realistic test data for all models with proper foreign key relationships

Run this script to populate the database with sample data for testing:
python seed.py
"""

import os
import sys
from datetime import datetime, timedelta
import json
import random

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import (
    User, Dog, Photo, Match, Message, Event, EventRegistration
)

def create_seed_data():
    """Main function to create all seed data"""
    
    print("🌱 Starting DogMatch database seeding...")
    
    # Clear existing data (optional - comment out if you want to keep existing data)
    print("🗑️  Clearing existing data...")
    clear_existing_data()
    
    # Create data in proper order (respecting foreign key dependencies)
    users = create_users()
    dogs = create_dogs(users)
    photos = create_photos(dogs)
    matches = create_matches(dogs)
    messages = create_messages(matches, users)
    events = create_events(users)
    event_registrations = create_event_registrations(events, users, dogs)
    
    print("✅ Database seeding completed successfully!")
    print(f"📊 Created:")
    print(f"   👥 {len(users)} users")
    print(f"   🐕 {len(dogs)} dogs")
    print(f"   📸 {len(photos)} photos")
    print(f"   💕 {len(matches)} matches")
    print(f"   💬 {len(messages)} messages")
    print(f"   🎉 {len(events)} events")
    print(f"   🎟️  {len(event_registrations)} event registrations")

def clear_existing_data():
    """Clear existing data from all tables (use with caution!)"""
    try:
        # Delete in reverse order of dependencies
        EventRegistration.query.delete()
        Event.query.delete()
        Message.query.delete()
        Match.query.delete()
        Photo.query.delete()
        Dog.query.delete()
        User.query.delete()
        
        db.session.commit()
        print("   ✅ Existing data cleared")
    except Exception as e:
        db.session.rollback()
        print(f"   ⚠️  Error clearing data: {e}")

def create_users():
    """Create sample users with different roles"""
    print("👥 Creating users...")
    
    users_data = [
        # Regular dog owners
        {
            'email': 'carlos.martinez@email.com',
            'username': 'carlos_mx',
            'password': 'SecurePass123!',
            'first_name': 'Carlos',
            'last_name': 'Martínez',
            'user_type': 'owner',
            'city': 'Mérida',
            'state': 'Yucatán',
            'country': 'México',
            'phone': '+52 999 123 4567'
        },
        {
            'email': 'ana.lopez@email.com',
            'username': 'ana_dogs',
            'password': 'SecurePass123!',
            'first_name': 'Ana',
            'last_name': 'López',
            'user_type': 'owner',
            'city': 'Cancún',
            'state': 'Quintana Roo',
            'country': 'México',
            'phone': '+52 998 234 5678'
        },
        {
            'email': 'miguel.rodriguez@email.com',
            'username': 'miguel_pets',
            'password': 'SecurePass123!',
            'first_name': 'Miguel',
            'last_name': 'Rodríguez',
            'user_type': 'owner',
            'city': 'Guadalajara',
            'state': 'Jalisco',
            'country': 'México',
            'phone': '+52 33 345 6789'
        },
        {
            'email': 'lucia.hernandez@email.com',
            'username': 'lucia_love_dogs',
            'password': 'SecurePass123!',
            'first_name': 'Lucía',
            'last_name': 'Hernández',
            'user_type': 'owner',
            'city': 'México',
            'state': 'Ciudad de México',
            'country': 'México',
            'phone': '+52 55 456 7890'
        },
        {
            'email': 'fernando.garcia@email.com',
            'username': 'fernando_k9',
            'password': 'SecurePass123!',
            'first_name': 'Fernando',
            'last_name': 'García',
            'user_type': 'owner',
            'city': 'Monterrey',
            'state': 'Nuevo León',
            'country': 'México',
            'phone': '+52 81 567 8901'
        },
        
        # Shelter users
        {
            'email': 'refugio.esperanza@shelter.org',
            'username': 'refugio_esperanza',
            'password': 'ShelterPass123!',
            'first_name': 'Refugio',
            'last_name': 'Esperanza',
            'user_type': 'shelter',
            'city': 'Mérida',
            'state': 'Yucatán',
            'country': 'México',
            'phone': '+52 999 111 2222'
        },
        {
            'email': 'patitas.felices@shelter.org',
            'username': 'patitas_felices',
            'password': 'ShelterPass123!',
            'first_name': 'Asociación',
            'last_name': 'Patitas Felices',
            'user_type': 'shelter',
            'city': 'Cancún',
            'state': 'Quintana Roo',
            'country': 'México',
            'phone': '+52 998 222 3333'
        },
        
        # Admin user
        {
            'email': 'admin@dogmatch.com',
            'username': 'admin_dogmatch',
            'password': 'AdminPass123!',
            'first_name': 'Admin',
            'last_name': 'DogMatch',
            'user_type': 'admin',
            'city': 'México',
            'state': 'Ciudad de México',
            'country': 'México',
            'phone': '+52 55 000 0000'
        }
    ]
    
    users = []
    for user_data in users_data:
        try:
            user = User(
                email=user_data['email'],
                username=user_data['username'],
                password=user_data['password'],
                user_type=user_data['user_type'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                city=user_data['city'],
                state=user_data['state'],
                country=user_data['country'],
                phone=user_data['phone'],
                is_verified=True,  # Mark as verified for testing
                is_active=True
            )
            
            db.session.add(user)
            users.append(user)
            
        except Exception as e:
            print(f"   ⚠️  Error creating user {user_data['username']}: {e}")
    
    db.session.commit()
    print(f"   ✅ Created {len(users)} users")
    return users

def create_dogs(users):
    """Create sample dogs for users"""
    print("🐕 Creating dogs...")
    
    # Filter users by type for proper assignment
    owners = [u for u in users if u.user_type == 'owner']
    shelters = [u for u in users if u.user_type == 'shelter']
    
    dogs_data = [
        # Dogs for regular owners
        {
            'name': 'Max',
            'owner': owners[0],  # Carlos
            'age': 3,
            'age_months': 6,
            'breed': 'Labrador Retriever',
            'gender': 'male',
            'size': 'large',
            'weight': 28.5,
            'color': 'Golden',
            'personality': ['Friendly', 'Energetic', 'Loyal', 'Playful'],
            'energy_level': 'high',
            'good_with_kids': True,
            'good_with_dogs': True,
            'good_with_cats': False,
            'is_vaccinated': True,
            'is_neutered': True,
            'description': 'Max es un Labrador muy cariñoso que ama jugar en el parque y nadar. Es perfecto para familias activas.',
            'location': 'Mérida, Yucatán',
            'availability_type': 'playdate'
        },
        {
            'name': 'Luna',
            'owner': owners[1],  # Ana
            'age': 2,
            'age_months': 0,
            'breed': 'Border Collie',
            'gender': 'female',
            'size': 'medium',
            'weight': 18.2,
            'color': 'Black and White',
            'personality': ['Intelligent', 'Active', 'Obedient', 'Alert'],
            'energy_level': 'very_high',
            'good_with_kids': True,
            'good_with_dogs': True,
            'good_with_cats': True,
            'is_vaccinated': True,
            'is_neutered': True,
            'description': 'Luna es una Border Collie súper inteligente que sabe muchos trucos y le encanta aprender.',
            'location': 'Cancún, Quintana Roo',
            'availability_type': 'playdate'
        },
        {
            'name': 'Rocky',
            'owner': owners[2],  # Miguel
            'age': 5,
            'age_months': 3,
            'breed': 'German Shepherd',
            'gender': 'male',
            'size': 'large',
            'weight': 35.0,
            'color': 'Brown and Black',
            'personality': ['Protective', 'Loyal', 'Confident', 'Courageous'],
            'energy_level': 'moderate',
            'good_with_kids': True,
            'good_with_dogs': False,
            'good_with_cats': False,
            'is_vaccinated': True,
            'is_neutered': True,
            'description': 'Rocky es un Pastor Alemán muy leal y protector. Ideal para quien busque un compañero fiel.',
            'location': 'Guadalajara, Jalisco',
            'availability_type': 'playdate'
        },
        {
            'name': 'Bella',
            'owner': owners[3],  # Lucía
            'age': 1,
            'age_months': 8,
            'breed': 'French Bulldog',
            'gender': 'female',
            'size': 'small',
            'weight': 9.5,
            'color': 'Fawn',
            'personality': ['Calm', 'Affectionate', 'Sociable', 'Gentle'],
            'energy_level': 'low',
            'good_with_kids': True,
            'good_with_dogs': True,
            'good_with_cats': True,
            'is_vaccinated': True,
            'is_neutered': False,
            'description': 'Bella es una Bulldog Francés muy tranquila y cariñosa, perfecta para apartamentos.',
            'location': 'México, Ciudad de México',
            'availability_type': 'playdate'
        },
        {
            'name': 'Thor',
            'owner': owners[4],  # Fernando
            'age': 4,
            'age_months': 0,
            'breed': 'Rottweiler',
            'gender': 'male',
            'size': 'extra_large',
            'weight': 50.0,
            'color': 'Black and Tan',
            'personality': ['Strong', 'Confident', 'Calm', 'Devoted'],
            'energy_level': 'moderate',
            'good_with_kids': True,
            'good_with_dogs': False,
            'good_with_cats': False,
            'is_vaccinated': True,
            'is_neutered': True,
            'description': 'Thor es un Rottweiler muy noble y protector. Necesita un dueño experimentado.',
            'location': 'Monterrey, Nuevo León',
            'availability_type': 'playdate'
        },
        
        # Dogs for adoption (shelter dogs)
        {
            'name': 'Canela',
            'owner': shelters[0],  # Refugio Esperanza
            'age': 2,
            'age_months': 6,
            'breed': 'Mixed Breed',
            'gender': 'female',
            'size': 'medium',
            'weight': 20.0,
            'color': 'Brown',
            'personality': ['Sweet', 'Gentle', 'Loving', 'Calm'],
            'energy_level': 'moderate',
            'good_with_kids': True,
            'good_with_dogs': True,
            'good_with_cats': True,
            'is_vaccinated': True,
            'is_neutered': True,
            'description': 'Canela es una perrita mestiza muy dulce que busca una familia amorosa.',
            'location': 'Mérida, Yucatán',
            'availability_type': 'adoption',
            'adoption_fee': 500.0
        },
        {
            'name': 'Simón',
            'owner': shelters[1],  # Patitas Felices
            'age': 1,
            'age_months': 4,
            'breed': 'Chihuahua Mix',
            'gender': 'male',
            'size': 'small',
            'weight': 3.5,
            'color': 'Cream',
            'personality': ['Playful', 'Alert', 'Brave', 'Loyal'],
            'energy_level': 'high',
            'good_with_kids': False,
            'good_with_dogs': True,
            'good_with_cats': True,
            'is_vaccinated': True,
            'is_neutered': True,
            'description': 'Simón es un Chihuahua muy valiente a pesar de su tamaño. Busca un hogar sin niños pequeños.',
            'location': 'Cancún, Quintana Roo',
            'availability_type': 'adoption',
            'adoption_fee': 300.0
        },
        {
            'name': 'Esperanza',
            'owner': shelters[0],  # Refugio Esperanza
            'age': 6,
            'age_months': 0,
            'breed': 'Pitbull Mix',
            'gender': 'female',
            'size': 'medium',
            'weight': 25.0,
            'color': 'Brindle',
            'personality': ['Loving', 'Patient', 'Gentle', 'Protective'],
            'energy_level': 'moderate',
            'good_with_kids': True,
            'good_with_dogs': False,
            'good_with_cats': False,
            'is_vaccinated': True,
            'is_neutered': True,
            'description': 'Esperanza es una perra senior muy cariñosa que busca un hogar tranquilo para sus años dorados.',
            'location': 'Mérida, Yucatán',
            'availability_type': 'adoption',
            'adoption_fee': 200.0
        }
    ]
    
    dogs = []
    for dog_data in dogs_data:
        try:
            dog = Dog(
                name=dog_data['name'],
                owner_id=dog_data['owner'].id,
                age=dog_data['age'],
                age_months=dog_data['age_months'],
                breed=dog_data['breed'],
                gender=dog_data['gender'],
                size=dog_data['size'],
                weight=dog_data['weight'],
                color=dog_data['color'],
                energy_level=dog_data['energy_level'],
                good_with_kids=dog_data['good_with_kids'],
                good_with_dogs=dog_data['good_with_dogs'],
                good_with_cats=dog_data['good_with_cats'],
                is_vaccinated=dog_data['is_vaccinated'],
                is_neutered=dog_data['is_neutered'],
                description=dog_data['description'],
                location=dog_data['location'],
                availability_type=dog_data['availability_type'],
                adoption_fee=dog_data.get('adoption_fee'),
                is_available=True,
                is_adopted=False
            )
            
            # Set personality traits
            dog.set_personality_list(dog_data['personality'])
            
            db.session.add(dog)
            dogs.append(dog)
            
        except Exception as e:
            print(f"   ⚠️  Error creating dog {dog_data['name']}: {e}")
    
    db.session.commit()
    print(f"   ✅ Created {len(dogs)} dogs")
    return dogs

def create_photos(dogs):
    """Create sample photos for dogs"""
    print("📸 Creating photos...")
    
    # Sample photo URLs (using placeholder images)
    photo_urls = [
        'https://images.unsplash.com/photo-1552053831-71594a27632d?w=500',  # Golden retriever
        'https://images.unsplash.com/photo-1551717743-49959800b1f6?w=500',  # Border collie
        'https://images.unsplash.com/photo-1589941013453-ec89f33b5e95?w=500',  # German shepherd
        'https://images.unsplash.com/photo-1583337130417-3346a1be7dee?w=500',  # French bulldog
        'https://images.unsplash.com/photo-1605568427561-40dd23c2acea?w=500',  # Rottweiler
        'https://images.unsplash.com/photo-1518717758536-85ae29035b6d?w=500',  # Mixed breed
        'https://images.unsplash.com/photo-1601758228041-f3b2795255f1?w=500',  # Chihuahua
        'https://images.unsplash.com/photo-1587300003388-59208cc962cb?w=500',  # Pitbull
        'https://images.unsplash.com/photo-1546975490-e8b92a360b24?w=500',  # Generic dog 1
        'https://images.unsplash.com/photo-1548199973-03cce0bbc87b?w=500',   # Generic dog 2
    ]
    
    photos = []
    for i, dog in enumerate(dogs):
        try:
            # Create 1-3 photos per dog
            num_photos = random.randint(1, 3)
            
            for j in range(num_photos):
                photo = Photo(
                    dog_id=dog.id,
                    url=photo_urls[i % len(photo_urls)] if j == 0 else photo_urls[(i + j) % len(photo_urls)],
                    filename=f"{dog.name.lower()}_{j+1}.jpg",
                    is_primary=(j == 0),  # First photo is primary
                    file_size=random.randint(50000, 500000),  # Random size
                    width=500,
                    height=500
                )
                
                db.session.add(photo)
                photos.append(photo)
                
        except Exception as e:
            print(f"   ⚠️  Error creating photos for dog {dog.name}: {e}")
    
    db.session.commit()
    print(f"   ✅ Created {len(photos)} photos")
    return photos

def create_matches(dogs):
    """Create sample matches between dogs"""
    print("💕 Creating matches...")
    
    # Only create matches between owner dogs (not shelter dogs)
    owner_dogs = [dog for dog in dogs if dog.owner.user_type == 'owner']
    
    matches = []
    
    # Create some specific interesting matches
    match_scenarios = [
        # Mutual matches (both liked each other)
        {
            'dog_one': owner_dogs[0],  # Max
            'dog_two': owner_dogs[1],  # Luna
            'dog_one_action': 'like',
            'dog_two_action': 'like',
            'status': 'matched'
        },
        {
            'dog_one': owner_dogs[2],  # Rocky
            'dog_two': owner_dogs[3],  # Bella
            'dog_one_action': 'super_like',
            'dog_two_action': 'like',
            'status': 'matched'
        },
        
        # Pending matches (one liked, waiting for response)
        {
            'dog_one': owner_dogs[0],  # Max
            'dog_two': owner_dogs[4],  # Thor
            'dog_one_action': 'like',
            'dog_two_action': 'pending',
            'status': 'pending'
        },
        {
            'dog_one': owner_dogs[1],  # Luna
            'dog_two': owner_dogs[2],  # Rocky
            'dog_one_action': 'super_like',
            'dog_two_action': 'pending',
            'status': 'pending'
        },
        
        # Declined matches
        {
            'dog_one': owner_dogs[3],  # Bella
            'dog_two': owner_dogs[4],  # Thor
            'dog_one_action': 'like',
            'dog_two_action': 'pass',
            'status': 'declined'
        }
    ]
    
    for match_data in match_scenarios:
        try:
            match = Match(
                dog_one_id=match_data['dog_one'].id,
                dog_two_id=match_data['dog_two'].id,
                initiated_by_dog_id=match_data['dog_one'].id,
                dog_one_action=match_data['dog_one_action'],
                dog_two_action=match_data['dog_two_action'],
                status=match_data['status'],
                match_type='playdate'
            )
            
            # Set matched_at for mutual matches
            if match_data['status'] == 'matched':
                match.matched_at = datetime.utcnow() - timedelta(days=random.randint(1, 30))
            
            # Set created_at to random past date
            match.created_at = datetime.utcnow() - timedelta(days=random.randint(1, 45))
            
            db.session.add(match)
            matches.append(match)
            
        except Exception as e:
            print(f"   ⚠️  Error creating match: {e}")
    
    db.session.commit()
    print(f"   ✅ Created {len(matches)} matches")
    return matches

def create_messages(matches, users):
    """Create sample messages for matched dogs"""
    print("💬 Creating messages...")
    
    # Only create messages for matched pairs
    matched_matches = [match for match in matches if match.status == 'matched']
    
    messages = []
    
    # Sample conversation starters and responses
    conversations = [
        [
            "¡Hola! Vi que a nuestros perros les gustó hacer match. Max es muy juguetón 🐕",
            "¡Qué genial! Luna también es súper activa. ¿Te gustaría que se conozcan en el parque?",
            "¡Me parece perfecto! ¿Conoces el Parque de las Américas? Ahí hay un área especial para perros",
            "¡Sí! Es perfecto. ¿Qué te parece el sábado por la mañana?",
            "Excelente, nos vemos el sábado a las 9 AM 🎾"
        ],
        [
            "¡Rocky y Bella hicieron match! 😊 Mi perro es muy tranquilo pero le gustan los paseos",
            "¡Qué bien! Bella es pequeñita pero muy valiente. Creo que se llevarían bien",
            "Perfecto. ¿Te parece si empezamos con un paseo corto para que se conozcan?",
            "Me parece ideal. ¿Conoces la Plaza de Armas? Es tranquila para un primer encuentro"
        ]
    ]
    
    for i, match in enumerate(matched_matches[:2]):  # Only first 2 matches
        conversation = conversations[i]
        
        # Get the dog owners
        dog_one_owner = match.dog_one.owner
        dog_two_owner = match.dog_two.owner
        
        for j, message_content in enumerate(conversation):
            try:
                # Alternate who sends each message
                sender = dog_one_owner if j % 2 == 0 else dog_two_owner
                
                message = Message(
                    match_id=match.id,
                    sender_user_id=sender.id,
                    content=message_content,
                    message_type='text',
                    is_read=j < len(conversation) - 1,  # Last message unread
                    sent_at=datetime.utcnow() - timedelta(days=random.randint(1, 7), hours=random.randint(0, 23), minutes=random.randint(0, 59))
                )
                
                db.session.add(message)
                messages.append(message)
                
            except Exception as e:
                print(f"   ⚠️  Error creating message: {e}")
    
    db.session.commit()
    print(f"   ✅ Created {len(messages)} messages")
    return messages

def create_events(users):
    """Create sample events"""
    print("🎉 Creating events...")
    
    # Get shelter and admin users for organizing events
    organizers = [u for u in users if u.user_type in ['shelter', 'admin']]
    
    events_data = [
        {
            'organizer': organizers[0],  # Refugio Esperanza
            'title': 'Jornada de Adopción - Encuentra tu Mejor Amigo',
            'description': 'Ven y conoce a nuestros perritos que buscan un hogar lleno de amor. Tenemos perros de todas las edades y tamaños esperándote.',
            'event_type': 'adoption',
            'event_date': datetime.utcnow() + timedelta(days=15),
            'duration_hours': 6.0,
            'location': 'Parque de las Américas, Mérida, Yucatán',
            'city': 'Mérida',
            'state': 'Yucatán',
            'max_participants': 50,
            'price': 0.0,
            'vaccination_required': True,
            'requires_approval': False,
            'contact_email': 'refugio.esperanza@shelter.org',
            'contact_phone': '+52 999 111 2222'
        },
        {
            'organizer': organizers[1],  # Patitas Felices
            'title': 'Entrenamiento Básico de Obediencia',
            'description': 'Aprende técnicas básicas de entrenamiento para mejorar la relación con tu mascota. Incluye comandos básicos y socialización.',
            'event_type': 'training',
            'event_date': datetime.utcnow() + timedelta(days=8),
            'duration_hours': 3.0,
            'location': 'Centro de Entrenamiento Canino, Cancún, Q.R.',
            'city': 'Cancún',
            'state': 'Quintana Roo',
            'max_participants': 15,
            'price': 350.0,
            'vaccination_required': True,
            'requires_approval': True,
            'contact_email': 'patitas.felices@shelter.org',
            'contact_phone': '+52 998 222 3333'
        },
        {
            'organizer': organizers[0],  # Refugio Esperanza
            'title': 'Encuentro Canino en el Parque',
            'description': 'Un día divertido para que tu perro socialice con otros perros mientras tú conoces otros amantes de las mascotas.',
            'event_type': 'meetup',
            'event_date': datetime.utcnow() + timedelta(days=5),
            'duration_hours': 4.0,
            'location': 'Parque Hundido, Mérida, Yucatán',
            'city': 'Mérida',
            'state': 'Yucatán',
            'max_participants': 30,
            'price': 0.0,
            'vaccination_required': True,
            'requires_approval': False,
            'contact_email': 'refugio.esperanza@shelter.org'
        },
        {
            'organizer': organizers[1],  # Patitas Felices
            'title': 'Competencia de Agilidad Canina',
            'description': 'Pon a prueba las habilidades de tu perro en nuestra competencia amistosa de agilidad. Premios para los ganadores.',
            'event_type': 'competition',
            'event_date': datetime.utcnow() + timedelta(days=22),
            'duration_hours': 5.0,
            'location': 'Club Canino Riviera Maya, Playa del Carmen, Q.R.',
            'city': 'Playa del Carmen',
            'state': 'Quintana Roo',
            'max_participants': 20,
            'price': 150.0,
            'vaccination_required': True,
            'requires_approval': True,
            'contact_email': 'patitas.felices@shelter.org'
        }
    ]
    
    events = []
    
    for event_data in events_data:
        try:
            event = Event(
                title=event_data['title'],
                event_date=event_data['event_date'],
                location=event_data['location'],
                organizer_id=event_data['organizer'].id,
                description=event_data['description'],
                category=event_data['event_type'],
                duration_hours=event_data['duration_hours'],
                city=event_data['city'],
                state=event_data['state'],
                country='México',
                max_participants=event_data['max_participants'],
                price=event_data['price'],
                currency='MXN',
                vaccination_required=event_data['vaccination_required'],
                requires_approval=event_data['requires_approval'],
                contact_email=event_data['contact_email'],
                contact_phone=event_data.get('contact_phone'),
                status='published',
                registration_deadline=event_data['event_date'] - timedelta(days=1)
            )
            
            db.session.add(event)
            events.append(event)
            
        except Exception as e:
            print(f"   ⚠️  Error creating event {event_data['title']}: {e}")
    
    db.session.commit()
    print(f"   ✅ Created {len(events)} events")
    return events

def create_event_registrations(events, users, dogs):
    """Create sample event registrations"""
    print("🎟️  Creating event registrations...")
    
    # Get owner users and their dogs
    owners = [u for u in users if u.user_type == 'owner']
    owner_dogs = [d for d in dogs if d.owner.user_type == 'owner']
    
    registrations = []
    
    # Create realistic registrations
    registration_scenarios = [
        # Confirmed registrations for adoption event
        {
            'event': events[0],  # Adoption event
            'user': owners[0],   # Carlos
            'dog': owner_dogs[0], # Max
            'status': 'confirmed',
            'payment_status': 'completed',
            'notes': 'Estamos interesados en conocer perros medianos para adopción.',
            'emergency_contact_name': 'María Martínez',
            'emergency_contact_phone': '+52 999 123 4568'
        },
        {
            'event': events[0],  # Adoption event
            'user': owners[1],   # Ana
            'dog': owner_dogs[1], # Luna
            'status': 'confirmed',
            'payment_status': 'completed',
            'notes': 'Luna es muy sociable y queremos ayudar con las adopciones.',
            'emergency_contact_name': 'Pedro López',
            'emergency_contact_phone': '+52 998 234 5679'
        },
        
        # Pending approval for training event
        {
            'event': events[1],  # Training event
            'user': owners[2],   # Miguel
            'dog': owner_dogs[2], # Rocky
            'status': 'pending',
            'payment_status': 'completed',
            'notes': 'Rocky necesita trabajar en socialización con otros perros.',
            'emergency_contact_name': 'Carmen Rodríguez',
            'emergency_contact_phone': '+52 33 345 6788'
        },
        {
            'event': events[1],  # Training event
            'user': owners[3],   # Lucía
            'dog': owner_dogs[3], # Bella
            'status': 'confirmed',
            'payment_status': 'completed',
            'notes': 'Bella es muy obediente pero queremos reforzar los comandos básicos.',
            'emergency_contact_name': 'Roberto Hernández',
            'emergency_contact_phone': '+52 55 456 7891'
        },
        
        # Meetup registrations (free event)
        {
            'event': events[2],  # Meetup
            'user': owners[0],   # Carlos
            'dog': owner_dogs[0], # Max
            'status': 'confirmed',
            'payment_status': 'completed',
            'notes': 'Max ama socializar en el parque.',
            'emergency_contact_name': 'María Martínez',
            'emergency_contact_phone': '+52 999 123 4568'
        },
        {
            'event': events[2],  # Meetup
            'user': owners[4],   # Fernando
            'dog': owner_dogs[4], # Thor
            'status': 'confirmed',
            'payment_status': 'completed',
            'notes': 'Thor necesita más socialización controlada.',
            'emergency_contact_name': 'Sandra García',
            'emergency_contact_phone': '+52 81 567 8902'
        },
        
        # Competition registration
        {
            'event': events[3],  # Competition
            'user': owners[1],   # Ana
            'dog': owner_dogs[1], # Luna
            'status': 'confirmed',
            'payment_status': 'completed',
            'notes': 'Luna es muy ágil y entrenada, esperamos hacer una buena competencia.',
            'emergency_contact_name': 'Pedro López',
            'emergency_contact_phone': '+52 998 234 5679'
        }
    ]
    
    for reg_data in registration_scenarios:
        try:
            registration = EventRegistration(
                event_id=reg_data['event'].id,
                user_id=reg_data['user'].id,
                dog_id=reg_data['dog'].id,
                status=reg_data['status'],
                payment_status=reg_data['payment_status'],
                payment_amount=reg_data['event'].price,
                payment_method='card' if reg_data['event'].price > 0 else None,
                payment_date=datetime.utcnow() - timedelta(days=random.randint(1, 7)) if reg_data['payment_status'] == 'completed' else None,
                notes=reg_data['notes'],
                emergency_contact_name=reg_data['emergency_contact_name'],
                emergency_contact_phone=reg_data['emergency_contact_phone'],
                registered_at=datetime.utcnow() - timedelta(days=random.randint(1, 10))
            )
            
            # Set confirmation date for confirmed registrations
            if reg_data['status'] == 'confirmed':
                registration.approved_at = datetime.utcnow() - timedelta(days=random.randint(0, 5))
            
            db.session.add(registration)
            registrations.append(registration)
            
        except Exception as e:
            print(f"   ⚠️  Error creating event registration: {e}")
    
    db.session.commit()
    
    # Update event participant counts
    for event in events:
        event.update_participant_count()
    
    print(f"   ✅ Created {len(registrations)} event registrations")
    return registrations

def update_match_message_stats(matches):
    """Update message statistics for matches"""
    print("📊 Updating match statistics...")
    
    try:
        for match in matches:
            match.update_message_stats()
        
        db.session.commit()
        print("   ✅ Match statistics updated")
        
    except Exception as e:
        print(f"   ⚠️  Error updating match stats: {e}")

if __name__ == '__main__':
    # Create Flask app context
    app = create_app()
    
    with app.app_context():
        try:
            create_seed_data()
            
            # Update statistics after all data is created
            print("📊 Updating statistics...")
            
            # Update message counts for matches
            matches = Match.query.all()
            update_match_message_stats(matches)
            
            print("\n🎉 Database seeding completed successfully!")
            print("\n📈 Final Statistics:")
            print(f"   👥 Users: {User.query.count()}")
            print(f"   🐕 Dogs: {Dog.query.count()}")
            print(f"   📸 Photos: {Photo.query.count()}")
            print(f"   💕 Matches: {Match.query.count()}")
            print(f"   💬 Messages: {Message.query.count()}")
            print(f"   🎉 Events: {Event.query.count()}")
            print(f"   🎟️  Event Registrations: {EventRegistration.query.count()}")
            
            print("\n🔐 Test User Credentials:")
            print("   Regular Users (password: SecurePass123!):")
            print("   - carlos.martinez@email.com (carlos_mx)")
            print("   - ana.lopez@email.com (ana_dogs)")
            print("   - miguel.rodriguez@email.com (miguel_pets)")
            print("   - lucia.hernandez@email.com (lucia_love_dogs)")
            print("   - fernando.garcia@email.com (fernando_k9)")
            print("\n   Shelter Users (password: ShelterPass123!):")
            print("   - refugio.esperanza@shelter.org (refugio_esperanza)")
            print("   - patitas.felices@shelter.org (patitas_felices)")
            print("\n   Admin User (password: AdminPass123!):")
            print("   - admin@dogmatch.com (admin_dogmatch)")
            
            print("\n🚀 Ready for API testing!")
            
        except Exception as e:
            print(f"❌ Error during seeding: {e}")
            db.session.rollback()
            raise