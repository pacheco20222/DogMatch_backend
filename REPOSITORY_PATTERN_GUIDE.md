# Repository Pattern Guide

## Overview
The Repository Pattern provides a data access layer that abstracts database queries from business logic. This makes code more testable, maintainable, and follows the Separation of Concerns principle.

## Architecture

```
Controllers/Routes        Services              Repositories         Database
    (HTTP)           (Business Logic)        (Data Access)         (SQLAlchemy)
      ↓                      ↓                      ↓                    ↓
  Validate Input   →   Business Rules    →    Query Building   →   Execute Query
  Call Service     ←   Use Repository    ←    Return Models    ←   Return Results
  Return Response
```

## Benefits

### 1. **Abstraction**
- Database queries hidden behind repository methods
- Easy to switch ORM or database
- Consistent query patterns across codebase

### 2. **Testability**
- Easy to mock repositories in unit tests
- No need for database in service tests
- Fast, isolated test execution

### 3. **Reusability**
- Same query methods used across services
- Centralized complex queries
- No duplicate query logic

### 4. **Maintainability**
- Database operations in one place
- Easy to optimize queries
- Clear data access contracts

## Repository Classes

### 1. UserRepository & BlacklistedTokenRepository

**Location:** `app/repositories/user_repository.py`

**Methods:**
- `find_by_id(user_id)` - Get user by ID
- `find_by_email(email)` - Get user by email (case-insensitive)
- `find_by_username(username)` - Get user by username
- `find_by_email_or_username(identifier)` - Get user by either
- `create(user_data)` - Create new user
- `update(user, updates)` - Update user attributes
- `delete(user)` - Delete user
- `search(query, limit, offset)` - Search by name/username
- `find_all(limit, offset)` - Get all users (paginated)
- `count()` - Count total users
- `find_verified_users(limit)` - Get verified users only
- `find_by_location(city, state, country)` - Location-based search
- `exists_by_email(email)` - Check email existence
- `exists_by_username(username)` - Check username existence

**BlacklistedTokenRepository Methods:**
- `create(jti, user_id, expires_at)` - Add token to blacklist
- `find_by_jti(jti)` - Find blacklisted token
- `is_blacklisted(jti)` - Check if token is blacklisted
- `delete_expired()` - Clean up expired tokens
- `delete_by_user(user_id)` - Remove all user's tokens

### 2. DogRepository & PhotoRepository

**Location:** `app/repositories/dog_repository.py`

**DogRepository Methods:**
- `find_by_id(dog_id)` - Get dog by ID
- `find_by_owner(owner_id)` - Get all dogs for owner
- `create(dog_data)` - Create new dog profile
- `update(dog, updates)` - Update dog attributes
- `delete(dog)` - Delete dog profile
- `find_available(limit, offset)` - Get available dogs
- `search(query, limit)` - Search by name/breed
- `find_by_filters(filters, limit, offset)` - Advanced filtering
- `find_by_breed(breed, limit)` - Filter by breed
- `find_by_size(size, limit)` - Filter by size
- `count_by_owner(owner_id)` - Count owner's dogs
- `count_available()` - Count available dogs
- `exists(dog_id)` - Check dog existence

**PhotoRepository Methods:**
- `find_by_id(photo_id)` - Get photo by ID
- `find_by_dog(dog_id)` - Get all photos for dog
- `find_primary(dog_id)` - Get primary photo
- `create(photo_data)` - Add new photo
- `update(photo, updates)` - Update photo attributes
- `delete(photo)` - Delete photo
- `unset_primary_for_dog(dog_id)` - Unset all primary flags
- `count_by_dog(dog_id)` - Count dog's photos

### 3. MatchRepository

**Location:** `app/repositories/match_repository.py`

**Methods:**
- `find_by_id(match_id)` - Get match by ID
- `find_between_dogs(dog_one_id, dog_two_id)` - Find match between dogs
- `find_by_dog(dog_id, status)` - Get all matches for dog
- `find_by_dogs(dog_ids, status)` - Get matches for multiple dogs
- `create(match_data)` - Create new match
- `update(match, updates)` - Update match attributes
- `delete(match)` - Delete match
- `find_matched(dog_ids)` - Get confirmed matches
- `find_pending_likes(dog_id)` - Get dogs that liked this dog
- `find_swiped_dog_ids(dog_id)` - Get IDs of swiped dogs
- `count_by_dog(dog_id, status)` - Count dog's matches
- `count_matches_for_dogs(dog_ids)` - Count matches for multiple dogs
- `count_pending_likes_for_dogs(dog_ids)` - Count pending likes
- `count_swipes_by_dogs(dog_ids)` - Count total swipes
- `find_by_status(status, limit, offset)` - Get matches by status
- `exists_between_dogs(dog_one_id, dog_two_id)` - Check match existence

### 4. EventRepository & EventRegistrationRepository

**Location:** `app/repositories/event_repository.py`

**EventRepository Methods:**
- `find_by_id(event_id)` - Get event by ID
- `find_by_organizer(organizer_id)` - Get organizer's events
- `create(event_data)` - Create new event
- `update(event, updates)` - Update event attributes
- `delete(event)` - Delete event
- `find_upcoming(limit, offset)` - Get upcoming events
- `find_by_status(status, limit, offset)` - Filter by status
- `find_by_category(category, limit)` - Filter by category
- `find_by_location(location, limit)` - Search by location
- `find_by_date_range(start_date, end_date)` - Date range filter
- `search(query, limit)` - Search title/description/location
- `find_by_filters(filters, limit, offset)` - Advanced filtering
- `count_by_organizer(organizer_id)` - Count organizer's events
- `count_by_status(status)` - Count by status
- `exists(event_id)` - Check event existence

**EventRegistrationRepository Methods:**
- `find_by_id(registration_id)` - Get registration by ID
- `find_by_event(event_id, status)` - Get event's registrations
- `find_by_user(user_id, status)` - Get user's registrations
- `find_by_user_and_event(user_id, event_id)` - Find specific registration
- `create(registration_data)` - Create new registration
- `update(registration, updates)` - Update registration
- `delete(registration)` - Delete registration
- `count_by_event(event_id, status)` - Count event registrations
- `count_by_user(user_id, status)` - Count user registrations
- `exists_for_user_and_event(user_id, event_id)` - Check registration

### 5. MessageRepository

**Location:** `app/repositories/message_repository.py`

**Methods:**
- `find_by_id(message_id)` - Get message by ID
- `find_by_match(match_id, limit, offset)` - Get match's messages
- `find_by_sender(sender_user_id, limit, offset)` - Get user's sent messages
- `find_latest_by_match(match_id)` - Get most recent message
- `create(message_data)` - Create new message
- `update(message, updates)` - Update message
- `delete(message)` - Delete message
- `mark_as_read(message)` - Mark single message as read
- `mark_multiple_as_read(message_ids)` - Bulk mark as read
- `find_unread_by_match(match_id, user_id)` - Get unread messages
- `count_by_match(match_id)` - Count match's messages
- `count_unread_by_match(match_id, user_id)` - Count unread in match
- `count_unread_by_user(user_id)` - Count total unread
- `find_by_sender_and_match(sender_user_id, match_id)` - Specific query
- `delete_by_match(match_id)` - Delete all match messages
- `find_recent_matches_with_messages(user_id, limit)` - Recent conversations
- `exists(message_id)` - Check message existence

## Usage Examples

### Basic CRUD Operations

```python
from app.repositories import UserRepository

# Create
user_data = {
    'email': 'user@example.com',
    'username': 'johndoe',
    'password_hash': hashed_password
}
user = UserRepository.create(user_data)

# Read
user = UserRepository.find_by_email('user@example.com')
user = UserRepository.find_by_id(123)

# Update
UserRepository.update(user, {'first_name': 'John', 'last_name': 'Doe'})

# Delete
UserRepository.delete(user)
```

### Using in Services

```python
# app/services/user_service.py
from app.repositories import UserRepository

class UserService:
    @staticmethod
    def create_user(email, password, username):
        # Check if email exists using repository
        if UserRepository.exists_by_email(email):
            raise ValueError("Email already registered")
        
        # Check if username exists
        if UserRepository.exists_by_username(username):
            raise ValueError("Username already taken")
        
        # Create user via repository
        user_data = {
            'email': email.lower(),
            'password_hash': generate_password_hash(password),
            'username': username
        }
        return UserRepository.create(user_data)
    
    @staticmethod
    def authenticate(email, password):
        # Find user via repository
        user = UserRepository.find_by_email(email)
        
        if not user:
            return None
        
        if not check_password_hash(user.password_hash, password):
            return None
        
        return user
```

### Complex Queries

```python
from app.repositories import DogRepository

# Advanced filtering
filters = {
    'breed': 'Golden Retriever',
    'size': 'large',
    'good_with_kids': True,
    'min_age': 1,
    'max_age': 5,
    'exclude_owner_id': current_user_id
}
dogs = DogRepository.find_by_filters(filters, limit=20)

# Search
results = DogRepository.search('golden', limit=10)

# Existence check
if DogRepository.exists(dog_id):
    # Dog exists
    pass
```

### Pagination

```python
from app.repositories import EventRepository

# Get page 1 (events 0-19)
page_1 = EventRepository.find_upcoming(limit=20, offset=0)

# Get page 2 (events 20-39)
page_2 = EventRepository.find_upcoming(limit=20, offset=20)

# Get page 3 (events 40-59)
page_3 = EventRepository.find_upcoming(limit=20, offset=40)
```

### Counting and Statistics

```python
from app.repositories import MatchRepository, DogRepository

# Get user's dogs
dogs = DogRepository.find_by_owner(user_id)
dog_ids = [dog.id for dog in dogs]

# Count matches
total_matches = MatchRepository.count_matches_for_dogs(dog_ids)

# Count pending likes
pending_likes = MatchRepository.count_pending_likes_for_dogs(dog_ids)

# Count swipes
total_swipes = MatchRepository.count_swipes_by_dogs(dog_ids)
```

## Testing with Repositories

### Unit Testing Services

```python
from unittest.mock import Mock, patch
from app.services import UserService

def test_create_user():
    # Mock the repository
    with patch('app.repositories.UserRepository') as mock_repo:
        # Setup mock behavior
        mock_repo.exists_by_email.return_value = False
        mock_repo.exists_by_username.return_value = False
        mock_repo.create.return_value = Mock(id=1, email='test@test.com')
        
        # Test service
        user = UserService.create_user('test@test.com', 'password', 'testuser')
        
        # Verify repository was called correctly
        mock_repo.exists_by_email.assert_called_once_with('test@test.com')
        mock_repo.exists_by_username.assert_called_once_with('testuser')
        assert user.email == 'test@test.com'
```

## Migration Guide

### Before (Direct Database Queries):

```python
# In service layer - BAD ❌
class DogService:
    @staticmethod
    def get_available_dogs(limit=50):
        # Direct SQLAlchemy query in service
        return Dog.query.filter_by(is_available=True).limit(limit).all()
```

### After (Using Repository):

```python
# In service layer - GOOD ✅
from app.repositories import DogRepository

class DogService:
    @staticmethod
    def get_available_dogs(limit=50):
        # Use repository method
        return DogRepository.find_available(limit=limit)
```

## Best Practices

### 1. **Keep Repositories Thin**
- Only database operations
- No business logic
- No validation (except query validation)

### 2. **Use Descriptive Method Names**
- `find_by_*` for single result queries
- `find_*` for multiple result queries
- `create`, `update`, `delete` for write operations
- `count_*` for counting queries
- `exists_*` for boolean checks

### 3. **Return Models, Not Dictionaries**
- Repositories return SQLAlchemy models
- Services convert to dictionaries if needed
- Consistent return types

### 4. **Handle Pagination Consistently**
- Use `limit` and `offset` parameters
- Return lists, not paginated objects
- Let services/routes handle pagination logic

### 5. **Use Type Hints (Optional)**
```python
from typing import Optional, List

def find_by_id(user_id: int) -> Optional[User]:
    return User.query.get(user_id)

def find_all(limit: int = 100) -> List[User]:
    return User.query.limit(limit).all()
```

## Summary

The Repository Pattern provides:
- ✅ **Clean data access layer** - Database queries isolated
- ✅ **Easy testing** - Mock repositories in unit tests
- ✅ **Reusable queries** - Same methods used everywhere
- ✅ **Consistent patterns** - Standard CRUD operations
- ✅ **Maintainable code** - Single place for query optimization
- ✅ **Database agnostic** - Easy to switch ORMs/databases

Combined with the Service Layer (Issue #11), the architecture is now:
```
Routes → Services → Repositories → Database
(HTTP)   (Business)  (Data Access)  (Storage)
```

This provides excellent separation of concerns and makes the codebase enterprise-ready!
