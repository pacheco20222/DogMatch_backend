# app/schemas/dog_schemas.py
"""
Marshmallow schemas for Dog and Photo model validation
Separated from models for better organization and testability
"""

from app import ma
from marshmallow import fields, validate, validates, ValidationError
import re


class DogCreateSchema(ma.Schema):
    """Schema for creating a new dog profile"""
    
    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    age_years = fields.Int(validate=validate.Range(min=0, max=30))
    breed = fields.Str(validate=validate.Length(max=100))
    gender = fields.Str(required=True, validate=validate.OneOf(['male', 'female']))
    size = fields.Str(required=True, validate=validate.OneOf(['small', 'medium', 'large', 'extra_large']))
    weight = fields.Float(validate=validate.Range(min=0.1, max=200.0))
    color = fields.Str(validate=validate.Length(max=50))
    personality = fields.List(fields.Str(), missing=[])
    energy_level = fields.Str(validate=validate.OneOf(['low', 'moderate', 'high', 'very_high']))
    good_with_kids = fields.Str(validate=validate.OneOf(['yes', 'no', 'not_sure']))
    good_with_dogs = fields.Str(validate=validate.OneOf(['yes', 'no', 'not_sure']))
    good_with_cats = fields.Str(validate=validate.OneOf(['yes', 'no', 'not_sure']))
    is_vaccinated = fields.Bool(missing=False)
    is_neutered = fields.Bool()
    health_notes = fields.Str()
    special_needs = fields.Str()
    description = fields.Str(validate=validate.Length(max=1000))
    location = fields.Str(validate=validate.Length(max=200))
    availability_type = fields.Str(validate=validate.OneOf(['playdate', 'adoption', 'both']), missing='playdate')
    adoption_fee = fields.Float(validate=validate.Range(min=0))
    
    @validates('name')
    def validate_name(self, value):
        """Validate dog name format"""
        if not value.strip():
            raise ValidationError('Name cannot be empty.')
        
        if not re.match(r"^[a-zA-Z\s\-']+$", value.strip()):
            raise ValidationError('Name can only contain letters, spaces, hyphens, and apostrophes.')


class DogUpdateSchema(ma.Schema):
    """Schema for updating dog profile"""
    
    name = fields.Str(validate=validate.Length(min=1, max=100))
    age_years = fields.Int(validate=validate.Range(min=0, max=30))
    breed = fields.Str(validate=validate.Length(max=100))
    size = fields.Str(validate=validate.OneOf(['small', 'medium', 'large', 'extra_large']))
    weight = fields.Float(validate=validate.Range(min=0.1, max=200.0))
    color = fields.Str(validate=validate.Length(max=50))
    personality = fields.List(fields.Str())
    energy_level = fields.Str(validate=validate.OneOf(['low', 'moderate', 'high', 'very_high']))
    good_with_kids = fields.Str(validate=validate.OneOf(['yes', 'no', 'not_sure']))
    good_with_dogs = fields.Str(validate=validate.OneOf(['yes', 'no', 'not_sure']))
    good_with_cats = fields.Str(validate=validate.OneOf(['yes', 'no', 'not_sure']))
    is_vaccinated = fields.Bool()
    is_neutered = fields.Bool()
    health_notes = fields.Str()
    special_needs = fields.Str()
    description = fields.Str(validate=validate.Length(max=1000))
    location = fields.Str(validate=validate.Length(max=200))
    is_available = fields.Bool()
    availability_type = fields.Str(validate=validate.OneOf(['playdate', 'adoption', 'both']))
    adoption_fee = fields.Float(validate=validate.Range(min=0))


class DogResponseSchema(ma.Schema):
    """Schema for dog API responses"""
    
    id = fields.Int()
    name = fields.Str()
    age_years = fields.Int()
    age_string = fields.Str()
    breed = fields.Str()
    gender = fields.Str()
    size = fields.Str()
    weight = fields.Float()
    color = fields.Str()
    personality = fields.List(fields.Str())
    energy_level = fields.Str()
    good_with_kids = fields.Str()
    good_with_dogs = fields.Str()
    good_with_cats = fields.Str()
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
    s3_key = fields.Str()
    is_primary = fields.Bool()
    file_size = fields.Int()
    width = fields.Int()
    height = fields.Int()
    content_type = fields.Str()
    is_s3_photo = fields.Bool()
    created_at = fields.DateTime()
