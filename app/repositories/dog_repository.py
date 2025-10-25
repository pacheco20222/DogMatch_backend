"""
Dog Repository

Handles all database operations for Dog and Photo models.
Provides methods for querying, creating, updating, and deleting dog profiles.
"""

from app import db
from app.models.dog import Dog, Photo
from app.models.user import User
from sqlalchemy import or_, and_
from sqlalchemy.orm import joinedload, selectinload
from datetime import datetime, timezone


class DogRepository:
    """Repository for Dog model data access"""
    
    @staticmethod
    def find_by_id(dog_id):
        """
        Find dog by ID
        
        Args:
            dog_id: Dog ID
            
        Returns:
            Dog or None
        """
        return Dog.query.get(dog_id)
    
    @staticmethod
    def find_by_owner(owner_id):
        """
        Find all dogs owned by a user
        
        Args:
            owner_id: User ID
            
        Returns:
            list: List of dogs
        """
        return Dog.query.filter_by(owner_id=owner_id).order_by(
            Dog.created_at.desc()
        ).all()
    
    @staticmethod
    def create(dog_data):
        """
        Create a new dog profile
        
        Args:
            dog_data: Dictionary of dog attributes
            
        Returns:
            Dog: Created dog object
        """
        dog = Dog(**dog_data)
        db.session.add(dog)
        db.session.commit()
        db.session.refresh(dog)
        return dog
    
    @staticmethod
    def update(dog, updates):
        """
        Update dog attributes
        
        Args:
            dog: Dog object to update
            updates: Dictionary of fields to update
            
        Returns:
            Dog: Updated dog object
        """
        for key, value in updates.items():
            if hasattr(dog, key):
                setattr(dog, key, value)
        
        dog.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        db.session.refresh(dog)
        return dog
    
    @staticmethod
    def delete(dog):
        """
        Delete a dog profile
        
        Args:
            dog: Dog object to delete
            
        Returns:
            bool: True if successful
        """
        db.session.delete(dog)
        db.session.commit()
        return True
    
    @staticmethod
    def find_available(limit=50, offset=0):
        """
        Find all available dogs for matching
        
        Args:
            limit: Maximum results to return
            offset: Number of results to skip
            
        Returns:
            list: List of available dogs
        """
        return Dog.query.filter_by(is_available=True).order_by(
            Dog.created_at.desc()
        ).limit(limit).offset(offset).all()
    
    @staticmethod
    def search(query, limit=20):
        """
        Search dogs by name or breed
        
        Args:
            query: Search string
            limit: Maximum results to return
            
        Returns:
            list: List of matching dogs
        """
        pattern = f"%{query}%"
        return Dog.query.filter(
            or_(
                Dog.name.ilike(pattern),
                Dog.breed.ilike(pattern)
            )
        ).filter_by(is_available=True).limit(limit).all()
    
    @staticmethod
    def find_by_filters(filters, limit=50, offset=0):
        """
        Find dogs with advanced filters
        
        Args:
            filters: Dictionary of filter criteria
            limit: Maximum results to return
            offset: Number of results to skip
            
        Returns:
            list: List of matching dogs
        """
        query = Dog.query.filter_by(is_available=True)
        
        if 'breed' in filters and filters['breed']:
            query = query.filter(Dog.breed.ilike(f"%{filters['breed']}%"))
        
        if 'size' in filters and filters['size']:
            query = query.filter_by(size=filters['size'])
        
        if 'gender' in filters and filters['gender']:
            query = query.filter_by(gender=filters['gender'])
        
        if 'min_age' in filters:
            query = query.filter(Dog.age >= filters['min_age'])
        
        if 'max_age' in filters:
            query = query.filter(Dog.age <= filters['max_age'])
        
        if 'energy_level' in filters and filters['energy_level']:
            query = query.filter_by(energy_level=filters['energy_level'])
        
        if 'good_with_kids' in filters and filters['good_with_kids']:
            query = query.filter_by(good_with_kids=True)
        
        if 'good_with_dogs' in filters and filters['good_with_dogs']:
            query = query.filter_by(good_with_dogs=True)
        
        if 'good_with_cats' in filters and filters['good_with_cats']:
            query = query.filter_by(good_with_cats=True)
        
        if 'is_vaccinated' in filters and filters['is_vaccinated']:
            query = query.filter_by(is_vaccinated=True)
        
        if 'is_neutered' in filters and filters['is_neutered']:
            query = query.filter_by(is_neutered=True)
        
        if 'owner_id' in filters:
            query = query.filter_by(owner_id=filters['owner_id'])
        
        if 'exclude_owner_id' in filters:
            query = query.filter(Dog.owner_id != filters['exclude_owner_id'])
        
        return query.order_by(Dog.created_at.desc()).limit(limit).offset(offset).all()
    
    @staticmethod
    def find_by_breed(breed, limit=20):
        """
        Find dogs by breed
        
        Args:
            breed: Breed name
            limit: Maximum results to return
            
        Returns:
            list: List of dogs
        """
        return Dog.query.filter(
            Dog.breed.ilike(f"%{breed}%")
        ).filter_by(is_available=True).limit(limit).all()
    
    @staticmethod
    def find_by_size(size, limit=20):
        """
        Find dogs by size
        
        Args:
            size: Size (small, medium, large, giant)
            limit: Maximum results to return
            
        Returns:
            list: List of dogs
        """
        return Dog.query.filter_by(
            size=size,
            is_available=True
        ).limit(limit).all()
    
    @staticmethod
    def count_by_owner(owner_id):
        """
        Count dogs owned by a user
        
        Args:
            owner_id: User ID
            
        Returns:
            int: Number of dogs
        """
        return Dog.query.filter_by(owner_id=owner_id).count()
    
    @staticmethod
    def count_available():
        """
        Count available dogs
        
        Returns:
            int: Number of available dogs
        """
        return Dog.query.filter_by(is_available=True).count()
    
    @staticmethod
    def exists(dog_id):
        """
        Check if dog exists
        
        Args:
            dog_id: Dog ID
            
        Returns:
            bool: True if exists
        """
        return db.session.query(
            Dog.query.filter_by(id=dog_id).exists()
        ).scalar()
    
    # ==================== OPTIMIZED METHODS (Prevent N+1 Queries) ====================
    
    @staticmethod
    def find_by_id_with_owner_and_photos(dog_id):
        """
        Find dog by ID with owner and photos eager loaded (prevents N+1)
        
        Args:
            dog_id: Dog ID
            
        Returns:
            Dog or None with owner and photos loaded
        """
        return Dog.query.options(
            joinedload(Dog.owner),
            selectinload(Dog.photos)
        ).get(dog_id)
    
    @staticmethod
    def find_by_owner_with_photos(owner_id):
        """
        Find all dogs by owner with photos eager loaded
        Optimized for owner's dog list display
        
        Args:
            owner_id: User ID
            
        Returns:
            list: List of dogs with photos loaded
        """
        return Dog.query.filter_by(
            owner_id=owner_id
        ).options(
            selectinload(Dog.photos)
        ).order_by(Dog.created_at.desc()).all()
    
    @staticmethod
    def find_available_with_owner_and_photos(limit=20, offset=0):
        """
        Find available dogs with owner and photos eager loaded
        Highly optimized for swipe/discovery screens
        
        Args:
            limit: Maximum results
            offset: Pagination offset
            
        Returns:
            list: List of dogs with relationships loaded
        """
        return Dog.query.filter_by(
            is_available=True
        ).options(
            joinedload(Dog.owner),
            selectinload(Dog.photos)
        ).order_by(Dog.created_at.desc()).limit(limit).offset(offset).all()
    
    @staticmethod
    def find_by_filters_with_relations(breed=None, size=None, age_min=None, 
                                        age_max=None, gender=None, limit=50):
        """
        Find dogs by multiple filters with owner and photos loaded
        Optimized for filtered search results
        
        Args:
            breed: Breed filter
            size: Size filter
            age_min: Minimum age
            age_max: Maximum age
            gender: Gender filter
            limit: Maximum results
            
        Returns:
            list: List of filtered dogs with relationships
        """
        query = Dog.query.filter_by(is_available=True)
        
        if breed:
            query = query.filter(Dog.breed.ilike(f"%{breed}%"))
        if size:
            query = query.filter_by(size=size)
        if gender:
            query = query.filter_by(gender=gender)
        if age_min is not None:
            query = query.filter(Dog.age >= age_min)
        if age_max is not None:
            query = query.filter(Dog.age <= age_max)
        
        return query.options(
            joinedload(Dog.owner),
            selectinload(Dog.photos)
        ).limit(limit).all()
    
    @staticmethod
    def search_with_relations(search_term, limit=20):
        """
        Search dogs by name or breed with owner and photos loaded
        Optimized for search results display
        
        Args:
            search_term: Search string
            limit: Maximum results
            
        Returns:
            list: List of matching dogs with relationships
        """
        return Dog.query.filter(
            and_(
                Dog.is_available == True,
                or_(
                    Dog.name.ilike(f"%{search_term}%"),
                    Dog.breed.ilike(f"%{search_term}%")
                )
            )
        ).options(
            joinedload(Dog.owner),
            selectinload(Dog.photos)
        ).limit(limit).all()


class PhotoRepository:
    """Repository for Photo model data access"""
    
    @staticmethod
    def find_by_id(photo_id):
        """
        Find photo by ID
        
        Args:
            photo_id: Photo ID
            
        Returns:
            Photo or None
        """
        return Photo.query.get(photo_id)
    
    @staticmethod
    def find_by_dog(dog_id):
        """
        Find all photos for a dog
        
        Args:
            dog_id: Dog ID
            
        Returns:
            list: List of photos ordered by primary first
        """
        return Photo.query.filter_by(dog_id=dog_id).order_by(
            Photo.is_primary.desc(),
            Photo.created_at.desc()
        ).all()
    
    @staticmethod
    def find_primary(dog_id):
        """
        Find primary photo for a dog
        
        Args:
            dog_id: Dog ID
            
        Returns:
            Photo or None
        """
        return Photo.query.filter_by(
            dog_id=dog_id,
            is_primary=True
        ).first()
    
    @staticmethod
    def create(photo_data):
        """
        Create a new photo
        
        Args:
            photo_data: Dictionary of photo attributes
            
        Returns:
            Photo: Created photo object
        """
        photo = Photo(**photo_data)
        db.session.add(photo)
        db.session.commit()
        db.session.refresh(photo)
        return photo
    
    @staticmethod
    def update(photo, updates):
        """
        Update photo attributes
        
        Args:
            photo: Photo object to update
            updates: Dictionary of fields to update
            
        Returns:
            Photo: Updated photo object
        """
        for key, value in updates.items():
            if hasattr(photo, key):
                setattr(photo, key, value)
        
        photo.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        db.session.refresh(photo)
        return photo
    
    @staticmethod
    def delete(photo):
        """
        Delete a photo
        
        Args:
            photo: Photo object to delete
            
        Returns:
            bool: True if successful
        """
        db.session.delete(photo)
        db.session.commit()
        return True
    
    @staticmethod
    def unset_primary_for_dog(dog_id):
        """
        Unset primary flag for all photos of a dog
        
        Args:
            dog_id: Dog ID
            
        Returns:
            int: Number of photos updated
        """
        count = Photo.query.filter_by(
            dog_id=dog_id,
            is_primary=True
        ).update({'is_primary': False})
        db.session.commit()
        return count
    
    @staticmethod
    def count_by_dog(dog_id):
        """
        Count photos for a dog
        
        Args:
            dog_id: Dog ID
            
        Returns:
            int: Number of photos
        """
        return Photo.query.filter_by(dog_id=dog_id).count()
