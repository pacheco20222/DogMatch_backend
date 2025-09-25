# app/models/event.py
from datetime import datetime, timedelta
from app import db, ma
from marshmallow import fields, validate, validates, ValidationError
import re

class Event(db.Model):
    """
    Event model for DogMatch application
    Handles dog-related events like meetups, training sessions, adoption fairs
    """
    
    # Table configuration
    __tablename__ = 'events'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Foreign key to User (organizer)
    organizer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Basic event information
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.Enum('meetup', 'training', 'adoption', 'competition', 'social', 'educational', name='event_category_enum'), 
                        nullable=False, default='meetup')
    
    # Event scheduling
    event_date = db.Column(db.DateTime, nullable=False)
    duration_hours = db.Column(db.Float, nullable=True)  # Event duration in hours
    registration_deadline = db.Column(db.DateTime, nullable=True)
    
    # Location information
    location = db.Column(db.String(300), nullable=False)  # Address or venue name
    city = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(100), nullable=True)
    country = db.Column(db.String(100), nullable=True, default='Mexico')
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    venue_details = db.Column(db.Text, nullable=True)  # Parking, accessibility info, etc.
    
    # Capacity and pricing
    max_participants = db.Column(db.Integer, nullable=True)
    current_participants = db.Column(db.Integer, default=0, nullable=False)
    price = db.Column(db.Float, default=0.0, nullable=False)  # Price in local currency
    currency = db.Column(db.String(3), default='MXN', nullable=False)  # Currency code
    
    # Event requirements and restrictions
    min_age_requirement = db.Column(db.Integer, nullable=True)  # Minimum dog age in months
    max_age_requirement = db.Column(db.Integer, nullable=True)  # Maximum dog age in months
    size_requirements = db.Column(db.Text, nullable=True)  # JSON array of allowed sizes
    breed_restrictions = db.Column(db.Text, nullable=True)  # JSON array of restricted breeds
    vaccination_required = db.Column(db.Boolean, default=True, nullable=False)
    special_requirements = db.Column(db.Text, nullable=True)  # Additional requirements
    
    # Event status and settings
    status = db.Column(db.Enum('draft', 'published', 'cancelled', 'completed', name='event_status_enum'), 
                      nullable=False, default='draft')
    is_recurring = db.Column(db.Boolean, default=False, nullable=False)
    recurrence_pattern = db.Column(db.String(50), nullable=True)  # 'weekly', 'monthly', etc.
    requires_approval = db.Column(db.Boolean, default=False, nullable=False)  # Manual approval needed
    
    # Event media
    image_url = db.Column(db.String(500), nullable=True)
    image_filename = db.Column(db.String(255), nullable=True)
    
    # Contact and additional info
    contact_email = db.Column(db.String(255), nullable=True)
    contact_phone = db.Column(db.String(20), nullable=True)
    additional_info = db.Column(db.Text, nullable=True)
    rules_and_guidelines = db.Column(db.Text, nullable=True)
    
    # Analytics and engagement
    view_count = db.Column(db.Integer, default=0, nullable=False)
    interest_count = db.Column(db.Integer, default=0, nullable=False)  # Users who marked "interested"
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    published_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    # organizer relationship created via backref in User model
    registrations = db.relationship('EventRegistration', backref='event', lazy='dynamic', cascade='all, delete-orphan')
    
    def __init__(self, title, event_date, location, organizer_id, **kwargs):
        """
        Initialize Event instance
        Required fields: title, event_date, location, organizer_id
        """
        self.title = title.strip()
        self.event_date = event_date
        self.location = location.strip()
        self.organizer_id = organizer_id
        
        # Set optional fields
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def get_size_requirements_list(self):
        """Get size requirements as a list"""
        if not self.size_requirements:
            return []
        
        import json
        try:
            return json.loads(self.size_requirements)
        except (json.JSONDecodeError, TypeError):
            return []
    
    def set_size_requirements_list(self, size_list):
        """Set size requirements from a list"""
        import json
        if size_list:
            self.size_requirements = json.dumps(size_list)
        else:
            self.size_requirements = None
    
    def get_breed_restrictions_list(self):
        """Get breed restrictions as a list"""
        if not self.breed_restrictions:
            return []
        
        import json
        try:
            return json.loads(self.breed_restrictions)
        except (json.JSONDecodeError, TypeError):
            return []
    
    def set_breed_restrictions_list(self, breed_list):
        """Set breed restrictions from a list"""
        import json
        if breed_list:
            self.breed_restrictions = json.dumps(breed_list)
        else:
            self.breed_restrictions = None
    
    def is_upcoming(self):
        """Check if event is in the future"""
        return self.event_date > datetime.utcnow()
    
    def is_past(self):
        """Check if event is in the past"""
        return self.event_date < datetime.utcnow()
    
    def is_today(self):
        """Check if event is today"""
        today = datetime.utcnow().date()
        event_date = self.event_date.date()
        return today == event_date
    
    def is_registration_open(self):
        """Check if registration is still open"""
        if self.status != 'published':
            return False
        
        if self.registration_deadline and datetime.utcnow() > self.registration_deadline:
            return False
        
        if self.max_participants and self.current_participants >= self.max_participants:
            return False
        
        return self.is_upcoming()
    
    def is_full(self):
        """Check if event has reached capacity"""
        return (self.max_participants and 
                self.current_participants >= self.max_participants)
    
    def can_be_edited_by(self, user_id):
        """Check if user can edit this event"""
        return self.organizer_id == user_id
    
    def can_be_cancelled_by(self, user_id):
        """Check if user can cancel this event"""
        # Organizer can cancel, or admin
        return (self.organizer_id == user_id or 
                self.organizer.is_admin())
    
    def publish_event(self):
        """Publish the event (make it visible to users)"""
        if self.status == 'draft':
            self.status = 'published'
            self.published_at = datetime.utcnow()
            db.session.commit()
    
    def cancel_event(self, reason=None):
        """Cancel the event"""
        self.status = 'cancelled'
        self.updated_at = datetime.utcnow()
        
        # TODO: Send notifications to registered users
        # TODO: Handle refunds if applicable
        
        db.session.commit()
    
    def complete_event(self):
        """Mark event as completed"""
        self.status = 'completed'
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def increment_view_count(self):
        """Increment view count when event is viewed"""
        self.view_count += 1
        db.session.commit()
    
    def increment_interest_count(self):
        """Increment interest count when user marks as interested"""
        self.interest_count += 1
        db.session.commit()
    
    def update_participant_count(self):
        """Update current participant count based on confirmed registrations"""
        # Import here to avoid circular imports
        from app.models.event_registration import EventRegistration
        confirmed_count = self.registrations.filter(
            EventRegistration.status == 'confirmed'
        ).count()
    
        self.current_participants = confirmed_count
        db.session.commit()
    
    def get_confirmed_registrations(self):
        """Get all confirmed registrations for this event"""
        from app.models.event_registration import EventRegistration
        return self.registrations.filter(
            EventRegistration.status == 'confirmed'
        ).all()
    
    def get_pending_registrations(self):
        """Get all pending registrations (if approval required)"""
        from app.models.event_registration import EventRegistration
        return self.registrations.filter(
            EventRegistration.status == 'pending'
        ).all()
    
    def is_user_registered(self, user_id):
        """Check if user is registered for this event"""
        from app.models.event_registration import EventRegistration
        registration = self.registrations.filter(
            EventRegistration.user_id == user_id
        ).first()
        return registration is not None
    
    def get_user_registration(self, user_id):
        """Get user's registration for this event"""
        from app.models.event_registration import EventRegistration
        return self.registrations.filter(
            EventRegistration.user_id == user_id
        ).first()
    
    def can_dog_participate(self, dog):
        """Check if a dog meets event requirements"""
        # Age requirements
        if self.min_age_requirement:
            dog_age_months = (dog.age or 0) * 12 + (dog.age_months or 0)
            if dog_age_months < self.min_age_requirement:
                return False, "Dog is too young for this event"
        
        if self.max_age_requirement:
            dog_age_months = (dog.age or 0) * 12 + (dog.age_months or 0)
            if dog_age_months > self.max_age_requirement:
                return False, "Dog is too old for this event"
        
        # Size requirements
        size_reqs = self.get_size_requirements_list()
        if size_reqs and dog.size not in size_reqs:
            return False, f"This event is only for {', '.join(size_reqs)} dogs"
        
        # Breed restrictions
        breed_restrictions = self.get_breed_restrictions_list()
        if breed_restrictions and dog.breed in breed_restrictions:
            return False, f"This breed is not allowed at this event"
        
        # Vaccination requirement
        if self.vaccination_required and not dog.is_vaccinated:
            return False, "Dog must be vaccinated to participate"
        
        return True, "Dog meets all requirements"
    
    def get_distance_to(self, user_location):
        """Calculate distance to user's location"""
        if not all([self.latitude, self.longitude, user_location.get('latitude'), user_location.get('longitude')]):
            return None
        
        import math
        
        lat1, lon1 = math.radians(self.latitude), math.radians(self.longitude)
        lat2, lon2 = math.radians(user_location['latitude']), math.radians(user_location['longitude'])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Earth's radius in kilometers
        r = 6371
        
        return r * c
    
    def to_dict(self, include_organizer=True, include_registrations=False, current_user_id=None):
        """
        Convert event to dictionary for JSON responses
        include_organizer: Whether to include organizer information
        include_registrations: Whether to include registration details
        current_user_id: ID of user viewing the event (affects perspective)
        """
        data = {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'event_date': self.event_date.isoformat() if self.event_date else None,
            'duration_hours': self.duration_hours,
            'registration_deadline': self.registration_deadline.isoformat() if self.registration_deadline else None,
            'location': self.location,
            'city': self.city,
            'state': self.state,
            'country': self.country,
            'venue_details': self.venue_details,
            'max_participants': self.max_participants,
            'current_participants': self.current_participants,
            'price': self.price,
            'currency': self.currency,
            'min_age_requirement': self.min_age_requirement,
            'max_age_requirement': self.max_age_requirement,
            'size_requirements': self.get_size_requirements_list(),
            'breed_restrictions': self.get_breed_restrictions_list(),
            'vaccination_required': self.vaccination_required,
            'special_requirements': self.special_requirements,
            'status': self.status,
            'is_recurring': self.is_recurring,
            'recurrence_pattern': self.recurrence_pattern,
            'requires_approval': self.requires_approval,
            'image_url': self.image_url,
            'contact_email': self.contact_email,
            'contact_phone': self.contact_phone,
            'additional_info': self.additional_info,
            'rules_and_guidelines': self.rules_and_guidelines,
            'view_count': self.view_count,
            'interest_count': self.interest_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'published_at': self.published_at.isoformat() if self.published_at else None,
            
            # Computed fields
            'is_upcoming': self.is_upcoming(),
            'is_past': self.is_past(),
            'is_today': self.is_today(),
            'is_registration_open': self.is_registration_open(),
            'is_full': self.is_full()
        }
        
        if include_organizer:
            data['organizer'] = {
                'id': self.organizer.id,
                'username': self.organizer.username,
                'full_name': self.organizer.get_full_name(),
                'user_type': self.organizer.user_type
            }
        
        if current_user_id:
            data.update({
                'is_organized_by_me': self.organizer_id == current_user_id,
                'can_edit': self.can_be_edited_by(current_user_id),
                'can_cancel': self.can_be_cancelled_by(current_user_id),
                'is_registered': self.is_user_registered(current_user_id)
            })
            
            user_registration = self.get_user_registration(current_user_id)
            if user_registration:
                data['my_registration'] = user_registration.to_dict()
        
        if include_registrations:
            data['registrations'] = [
                reg.to_dict(include_user=True) 
                for reg in self.get_confirmed_registrations()
            ]
            
            if self.requires_approval:
                data['pending_registrations'] = [
                    reg.to_dict(include_user=True)
                    for reg in self.get_pending_registrations()
                ]
        
        return data
    
    def __repr__(self):
        """String representation for debugging"""
        return f'<Event {self.id}: {self.title} ({self.event_date})>'


# Marshmallow Schemas for Event model
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
    state = fields.Str(validate=validate.Length(max=100))
    country = fields.Str(validate=validate.Length(max=100), missing='Mexico')
    latitude = fields.Float(validate=validate.Range(min=-90, max=90))
    longitude = fields.Float(validate=validate.Range(min=-180, max=180))
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
    state = fields.Str(validate=validate.Length(max=100))
    country = fields.Str(validate=validate.Length(max=100))
    latitude = fields.Float(validate=validate.Range(min=-90, max=90))
    longitude = fields.Float(validate=validate.Range(min=-180, max=180))
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
    state = fields.Str()
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
    state = fields.Str()
    country = fields.Str()
    upcoming_only = fields.Bool(missing=True)
    max_distance = fields.Float(validate=validate.Range(min=0, max=1000))  # kilometers
    user_latitude = fields.Float(validate=validate.Range(min=-90, max=90))
    user_longitude = fields.Float(validate=validate.Range(min=-180, max=180))
    price_max = fields.Float(validate=validate.Range(min=0))
    free_only = fields.Bool(missing=False)
    organizer_type = fields.Str(validate=validate.OneOf(['shelter', 'admin']))
    start_date = fields.DateTime()
    end_date = fields.DateTime()
    registration_open_only = fields.Bool(missing=False)
    limit = fields.Int(validate=validate.Range(min=1, max=100), missing=20)
    offset = fields.Int(validate=validate.Range(min=0), missing=0)
