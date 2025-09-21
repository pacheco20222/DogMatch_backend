# app/models/dog.py
from datetime import datetime
from app import db, ma
from marshmallow import fields, validate, validates, ValidationError
import re

class Dog(db.Model):
    __tablename__ = "dogs"
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Foreign key relates to our user table
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=True)  
    age_months = db.Column(db.Integer, nullable=True)
    breed = db.Column(db.String(100), nullable=True)
    gender = db.Column(db.Enum('male', 'female', name='dog_gender_enum'), nullable=False)
    size = db.Column(db.Enum('small', 'medium', 'large', 'extra_large', name='dog_size_enum'), nullable=False)
    weight = db.Column(db.Float, nullable=True)  # KG
    color = db.Column(db.String(50), nullable=True)
    
    # Personality & Behavior
    personality = db.Column(db.Text, nullable=True)  # JSON array of personality tags
    energy_level = db.Column(db.Enum('low', 'moderate', 'high', 'very_high', name='energy_level_enum'), nullable=True)
    good_with_kids = db.Column(db.Boolean, nullable=True)
    good_with_dogs = db.Column(db.Boolean, nullable=True)
    good_with_cats = db.Column(db.Boolean, nullable=True)
    
    # Health (Vaccines, special needs)
    is_vaccinated = db.Column(db.Boolean, default=False, nullable=False)
    is_neutered = db.Column(db.Boolean, nullable=True)
    health_notes = db.Column(db.Text, nullable=True)
    special_needs = db.Column(db.Text, nullable=True)
    
    description = db.Column(db.Text, nullable=True)
    
    location = db.Column(db.String(200), nullable=True)  # City, State format
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    
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
        if self.age is None and self.age_months is None:
            return "Age unknown"
        
        if self.age and self.age_months:
            if self.age == 0:
                return f"{self.age_months} months"
            else:
                return f"{self.age} years, {self.age_months} months"
        elif self.age:
            return f"{self.age} year{'s' if self.age != 1 else ''}"
        elif self.age_months:
            return f"{self.age_months} month{'s' if self.age_months != 1 else ''}"
        
        return "Age unknown"
    
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
        return primary_photo.url if primary_photo else '/static/images/default-dog.jpg'
    
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
        """Calculate distance to another dog (if both have coordinates)"""
        if not all([self.latitude, self.longitude, other_dog.latitude, other_dog.longitude]):
            return None
        
        # Simple distance calculation (Haversine formula would be more accurate)
        import math
        
        lat1, lon1 = math.radians(self.latitude), math.radians(self.longitude)
        lat2, lon2 = math.radians(other_dog.latitude), math.radians(other_dog.longitude)
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Earth's radius in kilometers
        r = 6371
        
        return r * c
    
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
            'age': self.age,
            'age_months': self.age_months,
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
            data['owner'] = {
                'id': self.owner.id,
                'username': self.owner.username,
                'full_name': self.owner.get_full_name(),
                'user_type': self.owner.user_type,
                'city': self.owner.city,
                'state': self.owner.state
            }
        
        if include_photos:
            data['photos'] = [
                {
                    'id': photo.id,
                    'url': photo.url,
                    'is_primary': photo.is_primary
                } for photo in self.photos
            ]
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
    url = db.Column(db.String(500), nullable=False)  # URL or file path
    filename = db.Column(db.String(255), nullable=True)  # Original filename
    is_primary = db.Column(db.Boolean, default=False, nullable=False)
    
    # Metadata
    file_size = db.Column(db.Integer, nullable=True)  # Size in bytes
    width = db.Column(db.Integer, nullable=True)
    height = db.Column(db.Integer, nullable=True)
    
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
    
    def to_dict(self):
        return {
            'id': self.id,
            'dog_id': self.dog_id,
            'url': self.url,
            'filename': self.filename,
            'is_primary': self.is_primary,
            'file_size': self.file_size,
            'width': self.width,
            'height': self.height,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        """String representation for debugging"""
        return f'<Photo {self.filename} (Dog: {self.dog_id})>'


class DogCreateSchema(ma.Schema):
    
    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    age = fields.Int(validate=validate.Range(min=0, max=30))
    age_months = fields.Int(validate=validate.Range(min=0, max=11))
    breed = fields.Str(validate=validate.Length(max=100))
    gender = fields.Str(required=True, validate=validate.OneOf(['male', 'female']))
    size = fields.Str(required=True, validate=validate.OneOf(['small', 'medium', 'large', 'extra_large']))
    weight = fields.Float(validate=validate.Range(min=0.1, max=200.0))
    color = fields.Str(validate=validate.Length(max=50))
    personality = fields.List(fields.Str(), missing=[])
    energy_level = fields.Str(validate=validate.OneOf(['low', 'moderate', 'high', 'very_high']))
    good_with_kids = fields.Bool()
    good_with_dogs = fields.Bool()
    good_with_cats = fields.Bool()
    is_vaccinated = fields.Bool(missing=False)
    is_neutered = fields.Bool()
    health_notes = fields.Str()
    special_needs = fields.Str()
    description = fields.Str(validate=validate.Length(max=1000))
    location = fields.Str(validate=validate.Length(max=200))
    latitude = fields.Float(validate=validate.Range(min=-90, max=90))
    longitude = fields.Float(validate=validate.Range(min=-180, max=180))
    availability_type = fields.Str(validate=validate.OneOf(['playdate', 'adoption', 'both']), missing='playdate')
    adoption_fee = fields.Float(validate=validate.Range(min=0))
    
    @validates('name')
    def validate_name(self, value):
        if not value.strip():
            raise ValidationError('Name cannot be empty.')
        
        if not re.match(r"^[a-zA-Z\s\-']+$", value.strip()):
            raise ValidationError('Name can only contain letters, spaces, hyphens, and apostrophes.')


class DogUpdateSchema(ma.Schema):
    
    name = fields.Str(validate=validate.Length(min=1, max=100))
    age = fields.Int(validate=validate.Range(min=0, max=30))
    age_months = fields.Int(validate=validate.Range(min=0, max=11))
    breed = fields.Str(validate=validate.Length(max=100))
    size = fields.Str(validate=validate.OneOf(['small', 'medium', 'large', 'extra_large']))
    weight = fields.Float(validate=validate.Range(min=0.1, max=200.0))
    color = fields.Str(validate=validate.Length(max=50))
    personality = fields.List(fields.Str())
    energy_level = fields.Str(validate=validate.OneOf(['low', 'moderate', 'high', 'very_high']))
    good_with_kids = fields.Bool()
    good_with_dogs = fields.Bool()
    good_with_cats = fields.Bool()
    is_vaccinated = fields.Bool()
    is_neutered = fields.Bool()
    health_notes = fields.Str()
    special_needs = fields.Str()
    description = fields.Str(validate=validate.Length(max=1000))
    location = fields.Str(validate=validate.Length(max=200))
    latitude = fields.Float(validate=validate.Range(min=-90, max=90))
    longitude = fields.Float(validate=validate.Range(min=-180, max=180))
    is_available = fields.Bool()
    availability_type = fields.Str(validate=validate.OneOf(['playdate', 'adoption', 'both']))
    adoption_fee = fields.Float(validate=validate.Range(min=0))


class DogResponseSchema(ma.Schema):
    
    id = fields.Int()
    name = fields.Str()
    age = fields.Int()
    age_months = fields.Int()
    age_string = fields.Str()
    breed = fields.Str()
    gender = fields.Str()
    size = fields.Str()
    weight = fields.Float()
    color = fields.Str()
    personality = fields.List(fields.Str())
    energy_level = fields.Str()
    good_with_kids = fields.Bool()
    good_with_dogs = fields.Bool()
    good_with_cats = fields.Bool()
    is_vaccinated = fields.Bool()
    is_neutered = fields.Bool()
    health_notes = fields.Str()
    special_needs = fields.Str()
    description = fields.Str()
    location = fields.Str()
    is_available = fields.Bool()
    availability_type = fields.Str()
    adoption_fee = fields.Float()
    is_adopted = fields.Bool()
    adopted_at = fields.DateTime()
    view_count = fields.Int()
    like_count = fields.Int()
    primary_photo_url = fields.Str()
    photos = fields.List(fields.Dict())
    owner = fields.Dict()
    created_at = fields.DateTime()
    updated_at = fields.DateTime()
    last_active = fields.DateTime()


class PhotoSchema(ma.Schema):
    """Schema for photo responses"""
    
    id = fields.Int()
    dog_id = fields.Int()
    url = fields.Str()
    filename = fields.Str()
    is_primary = fields.Bool()
    file_size = fields.Int()
    width = fields.Int()
    height = fields.Int()
    created_at = fields.DateTime()