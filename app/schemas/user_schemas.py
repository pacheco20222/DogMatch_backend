# app/schemas/user_schemas.py
"""
Marshmallow schemas for User model validation
Separated from models for better organization and testability
"""

from app import ma
from marshmallow import fields, validate, validates, ValidationError
import re


class UserRegistrationSchema(ma.Schema):
    """Schema for user registration validation"""
    
    email = fields.Email(required=True, validate=validate.Length(max=255))
    password = fields.Str(required=True, validate=validate.Length(min=8, max=128))
    username = fields.Str(required=True, validate=validate.Length(min=3, max=50))
    first_name = fields.Str(validate=validate.Length(max=50))
    last_name = fields.Str(validate=validate.Length(max=50))
    phone = fields.Str(validate=validate.Length(max=20))
    user_type = fields.Str(validate=validate.OneOf(['owner', 'shelter', 'admin']), missing='owner')
    city = fields.Str(validate=validate.Length(max=100))
    state = fields.Str(validate=validate.Length(max=100))
    country = fields.Str(validate=validate.Length(max=100), missing='Mexico')
    profile_photo_url = fields.Str(validate=validate.Length(max=500), allow_none=True)
    
    @validates('email')
    def validate_email(self, value):
        """Custom email validation"""
        from app.models.user import User
        if User.query.filter_by(email=value.lower()).first():
            raise ValidationError('Email already registered.')
    
    @validates('username')
    def validate_username(self, value):
        """Custom username validation"""
        from app.models.user import User
        
        # Check for valid characters (alphanumeric, underscore, hyphen)
        if not re.match(r'^[a-zA-Z0-9_-]+$', value):
            raise ValidationError('Username can only contain letters, numbers, underscores, and hyphens.')
        
        # Check if username is taken
        if User.query.filter_by(username=value).first():
            raise ValidationError('Username already taken.')
    
    @validates('phone')
    def validate_phone(self, value):
        """Basic phone validation"""
        if value and not re.match(r'^[\+\d\s\-\(\)]+$', value):
            raise ValidationError('Invalid phone number format.')


class UserLoginSchema(ma.Schema):
    """Schema for user login validation"""
    
    email = fields.Email(required=True)
    password = fields.Str(required=True)
    totp_token = fields.Str(validate=validate.Length(equal=6), allow_none=True)
    backup_code = fields.Str(validate=validate.Length(equal=8), allow_none=True)


class Setup2FASchema(ma.Schema):
    """Schema for 2FA setup"""
    
    totp_token = fields.Str(required=True, validate=validate.Length(equal=6))


class Verify2FASchema(ma.Schema):
    """Schema for 2FA verification"""
    
    totp_token = fields.Str(validate=validate.Length(equal=6), allow_none=True)
    backup_code = fields.Str(validate=validate.Length(equal=8), allow_none=True)


class UserUpdateSchema(ma.Schema):
    """Schema for user profile updates"""
    
    username = fields.Str(validate=validate.Length(min=3, max=50), allow_none=True)
    first_name = fields.Str(validate=validate.Length(max=50), allow_none=True)
    last_name = fields.Str(validate=validate.Length(max=50), allow_none=True)
    phone = fields.Str(validate=validate.Length(max=20), allow_none=True)
    city = fields.Str(validate=validate.Length(max=100), allow_none=True)
    state = fields.Str(validate=validate.Length(max=100), allow_none=True)
    country = fields.Str(validate=validate.Length(max=100), allow_none=True)
    profile_photo_url = fields.Str(validate=validate.Length(max=500), allow_none=True)
    profile_photo_filename = fields.Str(validate=validate.Length(max=255), allow_none=True)
    
    @validates('phone')
    def validate_phone(self, value):
        """Basic phone validation"""
        if value and not re.match(r'^[\+\d\s\-\(\)]+$', value):
            raise ValidationError('Invalid phone number format.')

    @validates('username')
    def validate_username(self, value):
        """Ensure username format and uniqueness"""
        if not value:
            return
        if not re.match(r'^[a-zA-Z0-9_-]+$', value):
            raise ValidationError('Username can only contain letters, numbers, underscores, and hyphens.')

        from app.models.user import User
        existing = User.query.filter_by(username=value).first()
        current_user_id = self.context.get('user_id')
        if existing and existing.id != current_user_id:
            raise ValidationError('Username already taken.')


class UserResponseSchema(ma.Schema):
    """Schema for user API responses"""
    
    id = fields.Int()
    username = fields.Str()
    email = fields.Email()
    first_name = fields.Str()
    last_name = fields.Str()
    full_name = fields.Str()
    phone = fields.Str()
    user_type = fields.Str()
    city = fields.Str()
    state = fields.Str()
    country = fields.Str()
    profile_photo_url = fields.Str()
    is_active = fields.Bool()
    is_verified = fields.Bool()
    is_2fa_enabled = fields.Bool()
    has_backup_codes = fields.Bool()
    unused_backup_codes_count = fields.Int()
    created_at = fields.DateTime()
    last_login = fields.DateTime()
