# app/models/dog.py
from datetime import datetime
from app import db

class Dog(db.Model):
    __tablename__ = "dogs"
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Foreign key relates to our user table
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    
    name = db.Column(db.String(100), nullable=False)
    age_years = db.Column(db.Integer, nullable=True)  # Age in years
    breed = db.Column(db.String(100), nullable=True)
    gender = db.Column(db.Enum('male', 'female', name='dog_gender_enum'), nullable=False)
    size = db.Column(db.Enum('small', 'medium', 'large', 'extra_large', name='dog_size_enum'), nullable=False)
    weight = db.Column(db.Float, nullable=True)  # Weight in KG
    color = db.Column(db.String(50), nullable=True)
    
    # Personality & Behavior
    personality = db.Column(db.Text, nullable=True)  # JSON array of personality tags
    energy_level = db.Column(db.Enum('low', 'moderate', 'high', 'very_high', name='energy_level_enum'), nullable=True)
    good_with_kids = db.Column(db.Enum('yes', 'no', 'not_sure', name='compatibility_enum'), nullable=True)
    good_with_dogs = db.Column(db.Enum('yes', 'no', 'not_sure', name='compatibility_enum'), nullable=True)
    good_with_cats = db.Column(db.Enum('yes', 'no', 'not_sure', name='compatibility_enum'), nullable=True)
    
    # Health (Vaccines, special needs)
    is_vaccinated = db.Column(db.Boolean, default=False, nullable=False)
    is_neutered = db.Column(db.Boolean, nullable=True)
    health_notes = db.Column(db.Text, nullable=True)
    special_needs = db.Column(db.Text, nullable=True)
    
    description = db.Column(db.Text, nullable=True)
    
    location = db.Column(db.String(200), nullable=True)  # City, State format
    
    # Availability & Status
    is_available = db.Column(db.Boolean, default=True, nullable=False)
    availability_type = db.Column(db.Enum('playdate', 'adoption', 'both', name='availability_type_enum'), nullable=False, default='playdate')
    
    # Adoption specific fields (for shelters)
    adoption_fee = db.Column(db.Float, nullable=True)  # Fee in local currency
    is_adopted = db.Column(db.Boolean, default=False, nullable=False)
    adopted_at = db.Column(db.DateTime, nullable=True)
    
    # Activity tracking
    view_count = db.Column(db.Integer, default=0, nullable=False)
    like_count = db.Column(db.Integer, default=0, nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_active = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    # owner relationship is created via backref in User model
    photos = db.relationship('Photo', backref='dog', lazy=True, cascade='all, delete-orphan')
    
    # Match relationships (we'll need to handle this carefully since it's many-to-many)
    # These will be populated when we create the Match model
    sent_matches = db.relationship('Match', foreign_keys='Match.dog_one_id', backref='dog_one', lazy='dynamic', cascade='all, delete-orphan')
    received_matches = db.relationship('Match', foreign_keys='Match.dog_two_id', backref='dog_two', lazy='dynamic', cascade='all, delete-orphan')
    
    def __init__(self, name, gender, size, owner_id, **kwargs):
        """
        Initialize Dog instance
        Required fields: name, gender, size, owner_id
        """
        self.name = name.strip()
        self.gender = gender
        self.size = size
        self.owner_id = owner_id
        
        # Set optional fields
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def get_age_string(self):
        """Return formatted age string"""
        if self.age_years is None:
            return "Age unknown"
        
        return f"{self.age_years} year{'s' if self.age_years != 1 else ''}"
    
    def get_personality_list(self):
        """Get personality tags as a list"""
        if not self.personality:
            return []
        
        import json
        try:
            return json.loads(self.personality)
        except (json.JSONDecodeError, TypeError):
            return []
    
    def set_personality_list(self, personality_list):
        """Set personality tags from a list"""
        import json
        if personality_list:
            self.personality = json.dumps(personality_list)
        else:
            self.personality = None
    
    def get_primary_photo(self):
        """Get the primary photo for this dog"""
        primary_photo = next((photo for photo in self.photos if photo.is_primary), None)
        return primary_photo or (self.photos[0] if self.photos else None)
    
    def get_primary_photo_url(self):
        """Get primary photo URL or default placeholder"""
        primary_photo = self.get_primary_photo()
        if primary_photo:
            # Use the photo's to_dict method to get signed URL
            return primary_photo.to_dict()['url']
        return '/static/images/default-dog.jpg'
    
    def increment_view_count(self):
        """Increment view count when dog profile is viewed"""
        self.view_count += 1
        self.last_active = datetime.utcnow()
        db.session.commit()
    
    def increment_like_count(self):
        """Increment like count when dog is swiped right"""
        self.like_count += 1
        db.session.commit()
    
    def is_owned_by(self, user):
        """Check if dog is owned by given user"""
        return self.owner_id == user.id
    
    def can_be_matched_with(self, other_dog):
        """Check if this dog can be matched with another dog"""
        # Can't match with own dogs
        if self.owner_id == other_dog.owner_id:
            return False
        
        # Both dogs must be available
        if not (self.is_available and other_dog.is_available):
            return False
        
        # Can't match if already adopted
        if self.is_adopted or other_dog.is_adopted:
            return False
        
        return True
    
    def get_distance_to(self, other_dog):
        """
        Calculate distance to another dog based on location strings
        Returns None - location-based matching removed
        """
        return None
    
    def mark_as_adopted(self, adopted_at=None):
        self.is_adopted = True
        self.is_available = False
        self.adopted_at = adopted_at or datetime.utcnow()
        db.session.commit()
    
    def to_dict(self, include_owner=False, include_photos=True, include_stats=False):
        """
        Convert dog to dictionary for JSON responses
        include_owner: Whether to include owner information
        include_photos: Whether to include photo URLs
        include_stats: Whether to include view/like counts
        """
        data = {
            'id': self.id,
            'name': self.name,
            'age_years': self.age_years,
            'age_string': self.get_age_string(),
            'breed': self.breed,
            'gender': self.gender,
            'size': self.size,
            'weight': self.weight,
            'color': self.color,
            'personality': self.get_personality_list(),
            'energy_level': self.energy_level,
            'good_with_kids': self.good_with_kids,
            'good_with_dogs': self.good_with_dogs,
            'good_with_cats': self.good_with_cats,
            'is_vaccinated': self.is_vaccinated,
            'is_neutered': self.is_neutered,
            'health_notes': self.health_notes,
            'special_needs': self.special_needs,
            'description': self.description,
            'location': self.location,
            'is_available': self.is_available,
            'availability_type': self.availability_type,
            'adoption_fee': self.adoption_fee,
            'is_adopted': self.is_adopted,
            'adopted_at': self.adopted_at.isoformat() if self.adopted_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_active': self.last_active.isoformat() if self.last_active else None
        }
        
        if include_owner:
            # Get owner's profile photo URL (signed URL if S3 key)
            owner_profile_photo_url = None
            if self.owner.profile_photo_url:
                # Check if it's an S3 key (starts with user-photos/) or already a URL
                if self.owner.profile_photo_url.startswith('user-photos/'):
                    # It's an S3 key - generate signed URL
                    try:
                        from app.services.s3_service import s3_service
                        from flask import current_app
                        owner_profile_photo_url = s3_service.get_photo_url(
                            self.owner.profile_photo_url, 
                            signed=True, 
                            expiration=604800  # 7 days
                        )
                        if not owner_profile_photo_url:
                            current_app.logger.warning(f"Failed to generate signed URL for owner {self.owner.id} profile photo: {self.owner.profile_photo_url}")
                    except Exception as e:
                        from flask import current_app
                        current_app.logger.error(f"Error generating signed URL for owner {self.owner.id} profile photo: {str(e)}")
                else:
                    # It's already a URL (legacy data or external URL)
                    owner_profile_photo_url = self.owner.profile_photo_url
            else:
                from flask import current_app
                current_app.logger.warning(f"⚠️ Owner {self.owner.id} ({self.owner.username}) has no profile_photo_url set in database")
            
            data['owner'] = {
                'id': self.owner.id,
                'username': self.owner.username,
                'first_name': self.owner.first_name,
                'last_name': self.owner.last_name,
                'full_name': self.owner.get_full_name(),
                'user_type': self.owner.user_type,
                'city': self.owner.city,
                'state': self.owner.state,
                'profile_photo_url': owner_profile_photo_url  # This will be None if no photo is set
            }
            
            # Debug logging - always log, even if None
            from flask import current_app
            current_app.logger.info(f"📸 Dog {self.id} owner {self.owner.id} ({self.owner.username}) profile_photo_url: {owner_profile_photo_url or 'NULL/None'}")
        
        if include_photos:
            # Use photo.to_dict() to get signed URLs
            data['photos'] = [photo.to_dict() for photo in self.photos]
            data['primary_photo_url'] = self.get_primary_photo_url()
        
        if include_stats:
            data.update({
                'view_count': self.view_count,
                'like_count': self.like_count
            })
        
        return data
    
    def __repr__(self):
        """String representation for debugging"""
        return f'<Dog {self.name} ({self.breed}, {self.size})>'


class Photo(db.Model):
    """
    Photo model for dog images
    Each dog can have multiple photos
    """
    
    __tablename__ = 'photos'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Foreign key to Dog
    dog_id = db.Column(db.Integer, db.ForeignKey('dogs.id'), nullable=False)
    
    # Photo information
    url = db.Column(db.String(500), nullable=False)  # S3 URL or file path
    filename = db.Column(db.String(255), nullable=True)  # Original filename
    s3_key = db.Column(db.String(500), nullable=True)  # S3 object key for easy deletion
    is_primary = db.Column(db.Boolean, default=False, nullable=False)
    
    # Metadata
    file_size = db.Column(db.Integer, nullable=True)  # Size in bytes
    width = db.Column(db.Integer, nullable=True)
    height = db.Column(db.Integer, nullable=True)
    content_type = db.Column(db.String(100), nullable=True)  # MIME type (image/jpeg, image/png, etc.)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def __init__(self, dog_id, url, **kwargs):
        """Initialize Photo instance"""
        self.dog_id = dog_id
        self.url = url

        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def set_as_primary(self):
        """Set this photo as primary and unset others"""
        Photo.query.filter(Photo.dog_id == self.dog_id, Photo.id != self.id)\
                  .update({'is_primary': False})
        
        self.is_primary = True
        db.session.commit()
    
    def is_s3_photo(self):
        """Check if this photo is stored in S3"""
        # Check if it's an S3 key (starts with dog-photos/) or a full S3 URL
        return (self.url.startswith('dog-photos/') or 
                (self.url.startswith('https://') and 's3' in self.url))
    
    def get_s3_key(self):
        """Get S3 key for this photo (if stored in S3)"""
        return self.s3_key
    
    def to_dict(self):
        # Generate signed URL for S3 photos
        photo_url = self.url
        if self.is_s3_photo():
            from app.services.s3_service import s3_service
            # Use s3_key if available, otherwise use url (which should be the S3 key)
            s3_key = self.s3_key or self.url
            signed_url = s3_service.get_photo_url(s3_key, signed=True, expiration=3600)
            if signed_url:
                photo_url = signed_url
        
        return {
            'id': self.id,
            'dog_id': self.dog_id,
            'url': photo_url,
            'filename': self.filename,
            's3_key': self.s3_key,
            'is_primary': self.is_primary,
            'file_size': self.file_size,
            'width': self.width,
            'height': self.height,
            'content_type': self.content_type,
            'is_s3_photo': self.is_s3_photo(),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        """String representation for debugging"""
        return f'<Photo {self.filename} (Dog: {self.dog_id})>'