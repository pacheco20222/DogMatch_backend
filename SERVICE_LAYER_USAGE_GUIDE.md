# Service Layer Usage Guide

## Overview
The service layer separates business logic from route handlers, making the code more maintainable, testable, and following the Single Responsibility Principle.

## Architecture

```
Routes (HTTP Layer)          Services (Business Logic)       Models (Data Layer)
    ↓                                ↓                              ↓
Validate Input          →    Process Business Rules    →     Database Operations
Return Response         ←    Return Data/Exceptions    ←     Query/Save Data
```

## Service Classes

### 1. UserService (`app/services/user_service.py`)

**Methods:**
- `create_user()` - Register new user with hashed password
- `authenticate()` - Login with email/password, handles account locking
- `update_profile()` - Update user information
- `change_password()` - Change user password with verification
- `setup_2fa()` - Initialize 2FA setup with TOTP secret
- `enable_2fa()` - Enable 2FA after code verification
- `disable_2fa()` - Disable 2FA with password confirmation
- `verify_email()` - Mark email as verified
- `get_user_by_id/email/username()` - User queries
- `search_users()` - Search users by name/username
- `blacklist_token()` - Add JWT to blacklist on logout

**Example Usage:**
```python
# In app/routes/auth.py
from app.services import UserService

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.json
    
    try:
        # Business logic handled by service
        user = UserService.create_user(
            email=data['email'],
            password=data['password'],
            username=data['username'],
            first_name=data.get('first_name'),
            last_name=data.get('last_name')
        )
        
        return jsonify(user.to_dict()), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
```

### 2. DogService (`app/services/dog_service.py`)

**Methods:**
- `create_dog()` - Create new dog profile
- `update_dog()` - Update dog information (with ownership check)
- `delete_dog()` - Delete dog profile (with ownership check)
- `add_photo()` - Add photo to dog profile
- `delete_photo()` - Remove photo from dog profile
- `set_availability()` - Update dog availability for matching
- `get_dog_by_id()` - Get single dog
- `get_dogs_by_owner()` - Get all dogs for a user
- `get_available_dogs()` - Get dogs for discovery (with filters)
- `search_dogs()` - Search by name/breed
- `get_dog_photos()` - Get all photos for a dog

**Example Usage:**
```python
# In app/routes/dogs.py
from app.services import DogService
from flask_jwt_extended import jwt_required, get_jwt_identity

@dogs_bp.route('/', methods=['POST'])
@jwt_required()
def create_dog():
    user_id = int(get_jwt_identity())
    data = request.json
    
    try:
        # Service handles all business logic
        dog = DogService.create_dog(user_id, data)
        return jsonify(dog.to_dict()), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
```

### 3. MatchService (`app/services/match_service.py`)

**Methods:**
- `swipe()` - Process like/pass action, creates mutual matches
- `get_matches_for_dog()` - Get all matches for a specific dog
- `get_matches_for_user()` - Get matches for all user's dogs
- `unmatch()` - Break a match (with ownership check)
- `get_match_by_id()` - Get single match
- `get_pending_swipes_for_dog()` - Get dogs that liked this dog
- `get_swipe_candidates()` - Get dogs to swipe on (excludes already swiped)
- `get_match_statistics()` - Get user's match stats

**Example Usage:**
```python
# In app/routes/matches.py
from app.services import MatchService

@matches_bp.route('/swipe', methods=['POST'])
@jwt_required()
def swipe_on_dog():
    user_id = int(get_jwt_identity())
    data = request.json
    
    try:
        result = MatchService.swipe(
            user_id=user_id,
            dog_id=data['dog_id'],
            target_dog_id=data['target_dog_id'],
            action=data['action']  # 'like' or 'pass'
        )
        
        return jsonify({
            'match': result['match'].to_dict(),
            'is_new_match': result['is_new_match'],
            'message': result['message']
        }), 200
        
    except (ValueError, PermissionError) as e:
        return jsonify({'error': str(e)}), 400
```

### 4. EventService (`app/services/event_service.py`)

**Methods:**
- `create_event()` - Create new event
- `update_event()` - Update event (with organizer check)
- `cancel_event()` - Cancel event (with organizer check)
- `delete_event()` - Delete event if no registrations
- `register_for_event()` - Register user/dog for event
- `cancel_registration()` - Cancel event registration
- `get_event_by_id()` - Get single event
- `get_upcoming_events()` - Get upcoming events (with filters)
- `get_events_by_organizer()` - Get user's created events
- `get_user_registrations()` - Get user's event registrations
- `get_event_attendees()` - Get attendee list (organizer only)
- `search_events()` - Search by title/description/location
- `get_event_statistics()` - Get event stats (organizer only)

**Example Usage:**
```python
# In app/routes/events.py
from app.services import EventService

@events_bp.route('/', methods=['POST'])
@jwt_required()
def create_event():
    user_id = int(get_jwt_identity())
    data = request.json
    
    try:
        event = EventService.create_event(user_id, data)
        return jsonify(event.to_dict()), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
```

## Benefits of Service Layer

### 1. **Separation of Concerns**
- Routes handle HTTP requests/responses only
- Services handle business logic and validation
- Models handle data structure and relationships

### 2. **Testability**
```python
# Easy to unit test services without Flask context
def test_create_user():
    user = UserService.create_user(
        email="test@example.com",
        password="password123",
        username="testuser"
    )
    assert user.email == "test@example.com"
    assert user.username == "testuser"
```

### 3. **Reusability**
- Same service methods can be used by multiple routes
- Services can call other services
- No duplicate business logic

### 4. **Authorization**
- Services handle ownership checks
- Consistent permission enforcement
- Prevents unauthorized operations

### 5. **Error Handling**
- Services raise meaningful exceptions
- Routes catch and return appropriate HTTP responses
- Consistent error patterns

## Migration Guide

### Before (Business Logic in Routes):
```python
@dogs_bp.route('/<int:dog_id>', methods=['PUT'])
@jwt_required()
def update_dog(dog_id):
    user_id = int(get_jwt_identity())
    data = request.json
    
    # Business logic mixed with route handler ❌
    dog = Dog.query.get_or_404(dog_id)
    
    if dog.owner_id != user_id:
        return jsonify({'error': 'Not authorized'}), 403
    
    for key, value in data.items():
        if hasattr(dog, key):
            setattr(dog, key, value)
    
    db.session.commit()
    return jsonify(dog.to_dict()), 200
```

### After (Using Service Layer):
```python
@dogs_bp.route('/<int:dog_id>', methods=['PUT'])
@jwt_required()
def update_dog(dog_id):
    user_id = int(get_jwt_identity())
    data = request.json
    
    try:
        # Service handles all business logic ✅
        dog = DogService.update_dog(dog_id, user_id, data)
        return jsonify(dog.to_dict()), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except PermissionError as e:
        return jsonify({'error': str(e)}), 403
```

## Exception Handling Pattern

Services raise Python exceptions, routes convert to HTTP responses:

```python
# Service raises exceptions
def update_dog(dog_id, owner_id, updates):
    if not dog:
        raise ValueError("Dog not found")  # → 404
    
    if dog.owner_id != owner_id:
        raise PermissionError("Not authorized")  # → 403
    
    return dog

# Route catches and converts
try:
    dog = DogService.update_dog(dog_id, user_id, data)
    return jsonify(dog.to_dict()), 200
except ValueError as e:
    return jsonify({'error': str(e)}), 404
except PermissionError as e:
    return jsonify({'error': str(e)}), 403
```

## Next Steps

To fully adopt the service layer pattern:

1. **Update existing routes** to use services instead of direct DB operations
2. **Write unit tests** for service methods
3. **Add more service methods** as needed for business logic
4. **Document** any complex business rules in service docstrings

## Summary

The service layer provides:
- ✅ Clean separation of concerns
- ✅ Easier testing and maintenance
- ✅ Consistent business logic
- ✅ Better code reusability
- ✅ Clear authorization patterns
- ✅ Meaningful error handling
