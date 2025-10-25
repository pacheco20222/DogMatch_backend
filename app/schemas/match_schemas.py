# app/schemas/match_schemas.py
"""
Marshmallow schemas for Match model validation
Separated from models for better organization and testability
"""

from app import ma
from marshmallow import fields, validate, validates, ValidationError


class SwipeActionSchema(ma.Schema):
    """Schema for processing swipe actions"""
    
    target_dog_id = fields.Int(required=True)
    action = fields.Str(required=True, validate=validate.OneOf(['like', 'pass', 'super_like']))
    
    @validates('target_dog_id')
    def validate_target_dog_id(self, value):
        """Validate that target dog exists and is available"""
        from app.models.dog import Dog
        
        dog = Dog.query.get(value)
        if not dog:
            raise ValidationError('Target dog not found.')
        
        if not dog.is_available:
            raise ValidationError('Target dog is not available for matching.')


class MatchResponseSchema(ma.Schema):
    """Schema for match API responses"""
    
    id = fields.Int()
    status = fields.Str()
    match_type = fields.Str()
    is_active = fields.Bool()
    is_archived = fields.Bool()
    message_count = fields.Int()
    created_at = fields.DateTime()
    matched_at = fields.DateTime()
    last_message_at = fields.DateTime()
    updated_at = fields.DateTime()
    
    # Dog information
    dog_one = fields.Dict()
    dog_two = fields.Dict()
    dog_one_action = fields.Str()
    dog_two_action = fields.Str()
    
    # User perspective (when current_user_id is provided)
    my_dog = fields.Dict()
    other_dog = fields.Dict()
    my_action = fields.Str()
    other_action = fields.Str()
    
    # Recent messages (optional)
    recent_messages = fields.List(fields.Dict())


class MatchListSchema(ma.Schema):
    """Schema for listing matches with filters"""
    
    status = fields.Str(validate=validate.OneOf(['pending', 'matched', 'declined', 'expired']))
    match_type = fields.Str(validate=validate.OneOf(['playdate', 'adoption', 'general']))
    include_archived = fields.Bool(missing=False)
    limit = fields.Int(validate=validate.Range(min=1, max=100), missing=20)
    offset = fields.Int(validate=validate.Range(min=0), missing=0)
