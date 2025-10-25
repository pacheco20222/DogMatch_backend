# app/schemas/event_registration_schemas.py
"""
Marshmallow schemas for EventRegistration model validation
Separated from models for better organization and testability
"""

from app import ma
from marshmallow import fields, validate, validates, ValidationError
import re


class EventRegistrationCreateSchema(ma.Schema):
    """Schema for creating new event registrations"""
    
    dog_id = fields.Int(required=False)
    notes = fields.Str(validate=validate.Length(max=500))
    special_requests = fields.Str(validate=validate.Length(max=500))
    emergency_contact_name = fields.Str(validate=validate.Length(max=100))
    emergency_contact_phone = fields.Str(validate=validate.Length(max=20))
    discount_code = fields.Str(validate=validate.Length(max=50))
    
    @validates('dog_id')
    def validate_dog_id(self, value):
        """Validate that dog exists and belongs to current user"""
        from app.models.dog import Dog
        from flask_jwt_extended import get_current_user
        
        dog = Dog.query.get(value)
        if not dog:
            raise ValidationError('Dog not found.')
        
        # This validation would need current user context
        # Will be handled in the route
    
    @validates('emergency_contact_phone')
    def validate_phone(self, value):
        """Basic phone validation"""
        if value and not re.match(r'^[\+\d\s\-\(\)]+$', value):
            raise ValidationError('Invalid phone number format.')


class EventRegistrationUpdateSchema(ma.Schema):
    """Schema for updating event registrations"""
    
    notes = fields.Str(validate=validate.Length(max=500))
    special_requests = fields.Str(validate=validate.Length(max=500))
    emergency_contact_name = fields.Str(validate=validate.Length(max=100))
    emergency_contact_phone = fields.Str(validate=validate.Length(max=20))
    
    @validates('emergency_contact_phone')
    def validate_phone(self, value):
        """Basic phone validation"""
        if value and not re.match(r'^[\+\d\s\-\(\)]+$', value):
            raise ValidationError('Invalid phone number format.')


class RegistrationApprovalSchema(ma.Schema):
    """Schema for approving/rejecting registrations"""
    
    action = fields.Str(required=True, validate=validate.OneOf(['approve', 'reject']))
    reason = fields.Str(validate=validate.Length(max=500))  # Required for rejection


class PaymentProcessSchema(ma.Schema):
    """Schema for processing payments"""
    
    payment_method = fields.Str(required=True, validate=validate.OneOf(['card', 'paypal', 'transfer', 'cash']))
    payment_reference = fields.Str(validate=validate.Length(max=100))


class EventRegistrationResponseSchema(ma.Schema):
    """Schema for event registration API responses"""
    
    id = fields.Int()
    event_id = fields.Int()
    user_id = fields.Int()
    dog_id = fields.Int()
    registration_code = fields.Str()
    status = fields.Str()
    notes = fields.Str()
    special_requests = fields.Str()
    payment_status = fields.Str()
    payment_amount = fields.Float()
    payment_method = fields.Str()
    payment_date = fields.DateTime()
    discount_code = fields.Str()
    discount_amount = fields.Float()
    discount_percentage = fields.Float()
    final_amount = fields.Float()
    checked_in = fields.Bool()
    check_in_time = fields.DateTime()
    checked_out = fields.Bool()
    check_out_time = fields.DateTime()
    attended = fields.Bool()
    approved_at = fields.DateTime()
    rejection_reason = fields.Str()
    emergency_contact_name = fields.Str()
    emergency_contact_phone = fields.Str()
    registered_at = fields.DateTime()
    updated_at = fields.DateTime()
    cancelled_at = fields.DateTime()
    
    # Related data (optional)
    event = fields.Dict()
    user = fields.Dict()
    dog = fields.Dict()
    
    # User perspective (when current_user_id provided)
    is_my_registration = fields.Bool()
    can_cancel = fields.Bool()
    can_approve = fields.Bool()
    is_eligible_for_refund = fields.Bool()


class RegistrationListSchema(ma.Schema):
    """Schema for listing registrations with filters"""
    
    event_id = fields.Int()
    status = fields.Str(validate=validate.OneOf(['pending', 'confirmed', 'rejected', 'cancelled', 'waitlisted']))
    payment_status = fields.Str(validate=validate.OneOf(['pending', 'completed', 'failed', 'refunded']))
    attended = fields.Bool()
    limit = fields.Int(validate=validate.Range(min=1, max=100), missing=50)
    offset = fields.Int(validate=validate.Range(min=0), missing=0)
