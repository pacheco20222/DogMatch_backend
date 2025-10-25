"""
Dog Service Layer

Handles all business logic related to dog profiles including:
- Dog creation and updates
- Photo management
- Availability management
- Dog searches and discovery
"""

from app import db
from app.models.dog import Dog, Photo
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


class DogService:
    """Service class for dog-related business logic"""
    
    @staticmethod
    def create_dog(owner_id, dog_data):
        """
        Create a new dog profile
        
        Args:
            owner_id: ID of the user who owns the dog
            dog_data: Dictionary containing dog information
            
        Returns:
            Dog: Created dog object
            
        Raises:
            ValueError: If validation fails
        """
        # Create dog instance
        dog = Dog(
            owner_id=owner_id,
            name=dog_data.get('name'),
            breed=dog_data.get('breed'),
            age=dog_data.get('age'),
            gender=dog_data.get('gender'),
            size=dog_data.get('size'),
            description=dog_data.get('description'),
            temperament=dog_data.get('temperament'),
            energy_level=dog_data.get('energy_level'),
            good_with_kids=dog_data.get('good_with_kids', False),
            good_with_dogs=dog_data.get('good_with_dogs', False),
            good_with_cats=dog_data.get('good_with_cats', False),
            health_notes=dog_data.get('health_notes'),
            special_needs=dog_data.get('special_needs'),
            is_vaccinated=dog_data.get('is_vaccinated', False),
            is_neutered=dog_data.get('is_neutered', False),
            is_available=dog_data.get('is_available', True),
            profile_photo=dog_data.get('profile_photo')
        )
        
        db.session.add(dog)
        db.session.commit()
        
        logger.info(f"Dog profile created: {dog.id} - {dog.name} (owner: {owner_id})")
        return dog
    
    @staticmethod
    def update_dog(dog_id, owner_id, updates):
        """
        Update dog profile
        
        Args:
            dog_id: Dog ID
            owner_id: Owner ID (for authorization check)
            updates: Dictionary of fields to update
            
        Returns:
            Dog: Updated dog object
            
        Raises:
            ValueError: If dog not found
            PermissionError: If user is not the owner
        """
        dog = Dog.query.get(dog_id)
        if not dog:
            raise ValueError("Dog not found")
        
        # Authorization check
        if dog.owner_id != owner_id:
            raise PermissionError("You are not authorized to update this dog profile")
        
        # Fields that can be updated
        allowed_fields = [
            'name', 'breed', 'age', 'gender', 'size', 'description',
            'temperament', 'energy_level', 'good_with_kids', 'good_with_dogs',
            'good_with_cats', 'health_notes', 'special_needs', 'is_vaccinated',
            'is_neutered', 'is_available', 'profile_photo'
        ]
        
        # Update allowed fields
        for key, value in updates.items():
            if key in allowed_fields and hasattr(dog, key):
                setattr(dog, key, value)
        
        dog.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        
        logger.info(f"Dog profile updated: {dog.id} - {dog.name}")
        return dog
    
    @staticmethod
    def delete_dog(dog_id, owner_id):
        """
        Delete dog profile
        
        Args:
            dog_id: Dog ID
            owner_id: Owner ID (for authorization check)
            
        Returns:
            bool: True if successful
            
        Raises:
            ValueError: If dog not found
            PermissionError: If user is not the owner
        """
        dog = Dog.query.get(dog_id)
        if not dog:
            raise ValueError("Dog not found")
        
        # Authorization check
        if dog.owner_id != owner_id:
            raise PermissionError("You are not authorized to delete this dog profile")
        
        db.session.delete(dog)
        db.session.commit()
        
        logger.info(f"Dog profile deleted: {dog_id}")
        return True
    
    @staticmethod
    def add_photo(dog_id, owner_id, photo_url, is_primary=False, caption=None):
        """
        Add photo to dog profile
        
        Args:
            dog_id: Dog ID
            owner_id: Owner ID (for authorization check)
            photo_url: URL of the uploaded photo
            is_primary: Whether this is the primary photo
            caption: Optional photo caption
            
        Returns:
            Photo: Created photo object
            
        Raises:
            ValueError: If dog not found
            PermissionError: If user is not the owner
        """
        dog = Dog.query.get(dog_id)
        if not dog:
            raise ValueError("Dog not found")
        
        # Authorization check
        if dog.owner_id != owner_id:
            raise PermissionError("You are not authorized to add photos to this dog")
        
        # If setting as primary, unset other primary photos
        if is_primary:
            Photo.query.filter_by(dog_id=dog_id, is_primary=True).update({'is_primary': False})
        
        # Create photo
        photo = Photo(
            dog_id=dog_id,
            photo_url=photo_url,
            is_primary=is_primary,
            caption=caption
        )
        
        db.session.add(photo)
        db.session.commit()
        
        logger.info(f"Photo added to dog: {dog_id}")
        return photo
    
    @staticmethod
    def delete_photo(photo_id, owner_id):
        """
        Delete photo from dog profile
        
        Args:
            photo_id: Photo ID
            owner_id: Owner ID (for authorization check)
            
        Returns:
            bool: True if successful
            
        Raises:
            ValueError: If photo not found
            PermissionError: If user is not the owner
        """
        photo = Photo.query.get(photo_id)
        if not photo:
            raise ValueError("Photo not found")
        
        # Get dog and check ownership
        dog = Dog.query.get(photo.dog_id)
        if not dog or dog.owner_id != owner_id:
            raise PermissionError("You are not authorized to delete this photo")
        
        db.session.delete(photo)
        db.session.commit()
        
        logger.info(f"Photo deleted: {photo_id}")
        return True
    
    @staticmethod
    def set_availability(dog_id, owner_id, is_available):
        """
        Set dog availability status
        
        Args:
            dog_id: Dog ID
            owner_id: Owner ID (for authorization check)
            is_available: True if available for matching
            
        Returns:
            Dog: Updated dog object
        """
        dog = Dog.query.get(dog_id)
        if not dog:
            raise ValueError("Dog not found")
        
        if dog.owner_id != owner_id:
            raise PermissionError("You are not authorized to update this dog")
        
        dog.is_available = is_available
        dog.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        
        logger.info(f"Dog availability updated: {dog.id} - available: {is_available}")
        return dog
    
    @staticmethod
    def get_dog_by_id(dog_id):
        """Get dog by ID"""
        return Dog.query.get(dog_id)
    
    @staticmethod
    def get_dogs_by_owner(owner_id):
        """Get all dogs owned by a user"""
        return Dog.query.filter_by(owner_id=owner_id).all()
    
    @staticmethod
    def get_available_dogs(limit=50, offset=0, filters=None):
        """
        Get available dogs for discovery/matching
        
        Args:
            limit: Maximum number of dogs to return
            offset: Number of dogs to skip (for pagination)
            filters: Optional dictionary of filters (breed, size, age, etc.)
            
        Returns:
            list: List of available dogs
        """
        query = Dog.query.filter_by(is_available=True)
        
        # Apply filters if provided
        if filters:
            if 'breed' in filters:
                query = query.filter(Dog.breed.ilike(f"%{filters['breed']}%"))
            
            if 'size' in filters:
                query = query.filter_by(size=filters['size'])
            
            if 'gender' in filters:
                query = query.filter_by(gender=filters['gender'])
            
            if 'min_age' in filters:
                query = query.filter(Dog.age >= filters['min_age'])
            
            if 'max_age' in filters:
                query = query.filter(Dog.age <= filters['max_age'])
            
            if 'good_with_kids' in filters and filters['good_with_kids']:
                query = query.filter_by(good_with_kids=True)
            
            if 'good_with_dogs' in filters and filters['good_with_dogs']:
                query = query.filter_by(good_with_dogs=True)
            
            if 'good_with_cats' in filters and filters['good_with_cats']:
                query = query.filter_by(good_with_cats=True)
            
            if 'energy_level' in filters:
                query = query.filter_by(energy_level=filters['energy_level'])
        
        # Order by created date (newest first)
        dogs = query.order_by(Dog.created_at.desc()).offset(offset).limit(limit).all()
        
        return dogs
    
    @staticmethod
    def search_dogs(search_query, limit=20):
        """
        Search dogs by name or breed
        
        Args:
            search_query: Search string
            limit: Maximum results to return
            
        Returns:
            list: List of matching dogs
        """
        pattern = f"%{search_query}%"
        dogs = Dog.query.filter(
            db.or_(
                Dog.name.ilike(pattern),
                Dog.breed.ilike(pattern)
            )
        ).filter_by(is_available=True).limit(limit).all()
        
        return dogs
    
    @staticmethod
    def get_dog_photos(dog_id):
        """Get all photos for a dog"""
        return Photo.query.filter_by(dog_id=dog_id).order_by(
            Photo.is_primary.desc(),
            Photo.created_at.desc()
        ).all()
