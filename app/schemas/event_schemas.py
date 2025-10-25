# app/schemas/event_schemas.py
"""
Marshmallow schemas for Event model validation
Separated from models for better organization and testability
"""

from app import ma
from marshmallow import fields, validate, validates, ValidationError
from datetime import datetime


class EventCreateSchema(ma.Schema):
    """Schema for creating new events"""
    
    title = fields.Str(required=True, validate=validate.Length(min=3, max=200))
    description = fields.Str(validate=validate.Length(max=2000))
    category = fields.Str(required=True, validate=validate.OneOf(['meetup', 'training', 'adoption', 'competition', 'social', 'educational']))
    event_date = fields.DateTime(required=True)
    duration_hours = fields.Float(validate=validate.Range(min=0.5, max=24))
    registration_deadline = fields.DateTime()
    location = fields.Str(required=True, validate=validate.Length(min=3, max=300))
    city = fields.Str(validate=validate.Length(max=100))
    country = fields.Str(validate=validate.Length(max=100), missing='Mexico')
    venue_details = fields.Str()
    max_participants = fields.Int(validate=validate.Range(min=1, max=1000))
    price = fields.Float(validate=validate.Range(min=0), missing=0.0)
    currency = fields.Str(validate=validate.Length(equal=3), missing='MXN')
    min_age_requirement = fields.Int(validate=validate.Range(min=1, max=300))  # months
    max_age_requirement = fields.Int(validate=validate.Range(min=1, max=300))  # months
    size_requirements = fields.List(fields.Str(validate=validate.OneOf(['small', 'medium', 'large', 'extra_large'])))
    breed_restrictions = fields.List(fields.Str())
    vaccination_required = fields.Bool(missing=True)
    special_requirements = fields.Str()
    requires_approval = fields.Bool(missing=False)
    contact_email = fields.Email()
    contact_phone = fields.Str(validate=validate.Length(max=20))
    additional_info = fields.Str()
    rules_and_guidelines = fields.Str()
    image_url = fields.Str()
    
    @validates('event_date')
    def validate_event_date(self, value):
        """Validate that event date is in the future"""
        # Convert to timezone-naive datetime for comparison
        if hasattr(value, 'replace'):
            compare_value = value.replace(tzinfo=None)
        else:
            compare_value = value
        
        if compare_value <= datetime.utcnow():
            raise ValidationError('Event date must be in the future.')
    
    @validates('registration_deadline')
    def validate_registration_deadline(self, value):
        """Validate that registration deadline is before event date"""
        # This validation needs access to event_date, so we'll handle it in the route
        pass
    
    @validates('title')
    def validate_title(self, value):
        """Validate event title"""
        if not value.strip():
            raise ValidationError('Event title cannot be empty.')


class EventUpdateSchema(ma.Schema):
    """Schema for updating events"""
    
    title = fields.Str(validate=validate.Length(min=3, max=200))
    description = fields.Str(validate=validate.Length(max=2000))
    category = fields.Str(validate=validate.OneOf(['meetup', 'training', 'adoption', 'competition', 'social', 'educational']))
    event_date = fields.DateTime()
    duration_hours = fields.Float(validate=validate.Range(min=0.5, max=24))
    registration_deadline = fields.DateTime()
    location = fields.Str(validate=validate.Length(min=3, max=300))
    city = fields.Str(validate=validate.Length(max=100))
    country = fields.Str(validate=validate.Length(max=100))
    venue_details = fields.Str()
    max_participants = fields.Int(validate=validate.Range(min=1, max=1000))
    price = fields.Float(validate=validate.Range(min=0))
    currency = fields.Str(validate=validate.Length(equal=3))
    min_age_requirement = fields.Int(validate=validate.Range(min=1, max=300))
    max_age_requirement = fields.Int(validate=validate.Range(min=1, max=300))
    size_requirements = fields.List(fields.Str(validate=validate.OneOf(['small', 'medium', 'large', 'extra_large'])))
    breed_restrictions = fields.List(fields.Str())
    vaccination_required = fields.Bool()
    special_requirements = fields.Str()
    requires_approval = fields.Bool()
    contact_email = fields.Email()
    contact_phone = fields.Str(validate=validate.Length(max=20))
    additional_info = fields.Str()
    rules_and_guidelines = fields.Str()
    image_url = fields.Str()


class EventResponseSchema(ma.Schema):
    """Schema for event API responses"""
    
    id = fields.Int()
    title = fields.Str()
    description = fields.Str()
    category = fields.Str()
    event_date = fields.DateTime()
    duration_hours = fields.Float()
    registration_deadline = fields.DateTime()
    location = fields.Str()
    city = fields.Str()
    country = fields.Str()
    venue_details = fields.Str()
    max_participants = fields.Int()
    current_participants = fields.Int()
    price = fields.Float()
    currency = fields.Str()
    min_age_requirement = fields.Int()
    max_age_requirement = fields.Int()
    size_requirements = fields.List(fields.Str())
    breed_restrictions = fields.List(fields.Str())
    vaccination_required = fields.Bool()
    special_requirements = fields.Str()
    status = fields.Str()
    is_recurring = fields.Bool()
    recurrence_pattern = fields.Str()
    requires_approval = fields.Bool()
    image_url = fields.Str()
    contact_email = fields.Email()
    contact_phone = fields.Str()
    additional_info = fields.Str()
    rules_and_guidelines = fields.Str()
    view_count = fields.Int()
    interest_count = fields.Int()
    created_at = fields.DateTime()
    updated_at = fields.DateTime()
    published_at = fields.DateTime()
    
    # Computed fields
    is_upcoming = fields.Bool()
    is_past = fields.Bool()
    is_today = fields.Bool()
    is_registration_open = fields.Bool()
    is_full = fields.Bool()
    
    # Organizer information
    organizer = fields.Dict()
    
    # User perspective (when current_user_id provided)
    is_organized_by_me = fields.Bool()
    can_edit = fields.Bool()
    can_cancel = fields.Bool()
    is_registered = fields.Bool()
    my_registration = fields.Dict()
    
    # Registrations (optional)
    registrations = fields.List(fields.Dict())
    pending_registrations = fields.List(fields.Dict())


class EventListSchema(ma.Schema):
    """Schema for listing events with filters"""
    
    category = fields.Str(validate=validate.OneOf(['meetup', 'training', 'adoption', 'competition', 'social', 'educational']))
    status = fields.Str(validate=validate.OneOf(['draft', 'published', 'cancelled', 'completed']))
    city = fields.Str()
    country = fields.Str()
    upcoming_only = fields.Bool(missing=True)
    price_max = fields.Float(validate=validate.Range(min=0))
    free_only = fields.Bool(missing=False)
    organizer_type = fields.Str(validate=validate.OneOf(['shelter', 'admin']))
    start_date = fields.DateTime()
    end_date = fields.DateTime()
    registration_open_only = fields.Bool(missing=False)
    limit = fields.Int(validate=validate.Range(min=1, max=100), missing=20)
    offset = fields.Int(validate=validate.Range(min=0), missing=0)
