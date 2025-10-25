# app/schemas/message_schemas.py
"""
Marshmallow schemas for Message model validation
Separated from models for better organization and testability
"""

from app import ma
from marshmallow import fields, validate, validates, ValidationError


class MessageCreateSchema(ma.Schema):
    """Schema for creating new messages"""
    
    content = fields.Str(required=True, validate=validate.Length(min=1, max=2000))
    message_type = fields.Str(validate=validate.OneOf(['text', 'image', 'location']), missing='text')
    
    # For image messages
    image_url = fields.Str(validate=validate.Length(max=500))
    image_filename = fields.Str(validate=validate.Length(max=255))
    
    # For location messages
    latitude = fields.Float(validate=validate.Range(min=-90, max=90))
    longitude = fields.Float(validate=validate.Range(min=-180, max=180))
    location_name = fields.Str(validate=validate.Length(max=200))
    
    @validates('content')
    def validate_content(self, value):
        """Validate message content"""
        if not value or not value.strip():
            raise ValidationError('Message content cannot be empty.')


class MessageUpdateSchema(ma.Schema):
    """Schema for editing messages"""
    
    content = fields.Str(required=True, validate=validate.Length(min=1, max=2000))
    
    @validates('content')
    def validate_content(self, value):
        """Validate message content"""
        if not value or not value.strip():
            raise ValidationError('Message content cannot be empty.')


class MessageResponseSchema(ma.Schema):
    """Schema for message API responses"""
    
    id = fields.Int()
    match_id = fields.Int()
    content = fields.Str()
    raw_content = fields.Str()
    message_type = fields.Str()
    is_read = fields.Bool()
    is_edited = fields.Bool()
    is_deleted = fields.Bool()
    sent_at = fields.DateTime()
    delivered_at = fields.DateTime()
    read_at = fields.DateTime()
    edited_at = fields.DateTime()
    
    # Sender information
    sender = fields.Dict()
    
    # User perspective
    is_sent_by_me = fields.Bool()
    can_edit = fields.Bool()
    can_delete = fields.Bool()
    
    # Media content (conditional)
    image_url = fields.Str()
    image_filename = fields.Str()
    latitude = fields.Float()
    longitude = fields.Float()
    location_name = fields.Str()
    system_data = fields.Str()
    
    # Match information (optional)
    match = fields.Dict()


class MessageListSchema(ma.Schema):
    """Schema for listing messages with filters"""
    
    match_id = fields.Int(required=False)  # Not required since it's in the URL path
    limit = fields.Int(validate=validate.Range(min=1, max=100), missing=50)
    offset = fields.Int(validate=validate.Range(min=0), missing=0)
    before_message_id = fields.Int()  # For pagination
    include_deleted = fields.Bool(missing=False)
    mark_as_read = fields.Bool(missing=True)  # Auto-mark messages as read when fetched
