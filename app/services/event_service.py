"""
Event Service Layer

Handles all business logic related to events including:
- Event creation and management
- Event registration
- Event searches and queries
- Attendee management
"""

from app import db
from app.models.event import Event
from app.models.event_registration import EventRegistration
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


class EventService:
    """Service class for event-related business logic"""
    
    @staticmethod
    def create_event(organizer_id, event_data):
        """
        Create a new event
        
        Args:
            organizer_id: ID of the user creating the event
            event_data: Dictionary containing event information
            
        Returns:
            Event: Created event object
            
        Raises:
            ValueError: If validation fails
        """
        event = Event(
            organizer_id=organizer_id,
            title=event_data.get('title'),
            description=event_data.get('description'),
            event_date=event_data.get('event_date'),
            event_time=event_data.get('event_time'),
            location=event_data.get('location'),
            location_details=event_data.get('location_details'),
            latitude=event_data.get('latitude'),
            longitude=event_data.get('longitude'),
            category=event_data.get('category'),
            max_attendees=event_data.get('max_attendees'),
            event_photo=event_data.get('event_photo'),
            status='upcoming'
        )
        
        db.session.add(event)
        db.session.commit()
        
        logger.info(f"Event created: {event.id} - {event.title} by user {organizer_id}")
        return event
    
    @staticmethod
    def update_event(event_id, organizer_id, updates):
        """
        Update event information
        
        Args:
            event_id: Event ID
            organizer_id: Organizer ID (for authorization)
            updates: Dictionary of fields to update
            
        Returns:
            Event: Updated event object
            
        Raises:
            ValueError: If event not found
            PermissionError: If user is not the organizer
        """
        event = Event.query.get(event_id)
        if not event:
            raise ValueError("Event not found")
        
        # Authorization check
        if event.organizer_id != organizer_id:
            raise PermissionError("You are not authorized to update this event")
        
        # Can't update past events
        if event.status == 'completed':
            raise ValueError("Cannot update completed events")
        
        # Fields that can be updated
        allowed_fields = [
            'title', 'description', 'event_date', 'event_time',
            'location', 'location_details', 'latitude', 'longitude',
            'category', 'max_attendees', 'event_photo', 'status'
        ]
        
        # Update allowed fields
        for key, value in updates.items():
            if key in allowed_fields and hasattr(event, key):
                setattr(event, key, value)
        
        event.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        
        logger.info(f"Event updated: {event.id} - {event.title}")
        return event
    
    @staticmethod
    def cancel_event(event_id, organizer_id, reason=None):
        """
        Cancel an event
        
        Args:
            event_id: Event ID
            organizer_id: Organizer ID (for authorization)
            reason: Optional cancellation reason
            
        Returns:
            Event: Cancelled event object
            
        Raises:
            ValueError: If event not found
            PermissionError: If user is not the organizer
        """
        event = Event.query.get(event_id)
        if not event:
            raise ValueError("Event not found")
        
        if event.organizer_id != organizer_id:
            raise PermissionError("You are not authorized to cancel this event")
        
        if event.status == 'completed':
            raise ValueError("Cannot cancel completed events")
        
        event.status = 'cancelled'
        event.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        
        logger.info(f"Event cancelled: {event.id} - {event.title}")
        return event
    
    @staticmethod
    def delete_event(event_id, organizer_id):
        """
        Delete an event
        
        Args:
            event_id: Event ID
            organizer_id: Organizer ID (for authorization)
            
        Returns:
            bool: True if successful
            
        Raises:
            ValueError: If event not found or has registrations
            PermissionError: If user is not the organizer
        """
        event = Event.query.get(event_id)
        if not event:
            raise ValueError("Event not found")
        
        if event.organizer_id != organizer_id:
            raise PermissionError("You are not authorized to delete this event")
        
        # Check if event has registrations
        registration_count = EventRegistration.query.filter_by(event_id=event_id).count()
        if registration_count > 0:
            raise ValueError("Cannot delete event with registrations. Cancel it instead.")
        
        db.session.delete(event)
        db.session.commit()
        
        logger.info(f"Event deleted: {event_id}")
        return True
    
    @staticmethod
    def register_for_event(event_id, user_id, dog_id, notes=None):
        """
        Register for an event
        
        Args:
            event_id: Event ID
            user_id: User ID
            dog_id: Dog ID (optional, depends on event type)
            notes: Optional registration notes
            
        Returns:
            EventRegistration: Created registration object
            
        Raises:
            ValueError: If validation fails
        """
        event = Event.query.get(event_id)
        if not event:
            raise ValueError("Event not found")
        
        # Check if event is cancelled
        if event.status == 'cancelled':
            raise ValueError("Cannot register for cancelled events")
        
        # Check if event is full
        if event.max_attendees:
            current_attendees = EventRegistration.query.filter_by(
                event_id=event_id,
                status='confirmed'
            ).count()
            
            if current_attendees >= event.max_attendees:
                raise ValueError("Event is full")
        
        # Check if already registered
        existing_registration = EventRegistration.query.filter_by(
            event_id=event_id,
            user_id=user_id
        ).first()
        
        if existing_registration:
            raise ValueError("Already registered for this event")
        
        # Create registration
        registration = EventRegistration(
            event_id=event_id,
            user_id=user_id,
            dog_id=dog_id,
            notes=notes,
            status='confirmed'
        )
        
        db.session.add(registration)
        db.session.commit()
        
        logger.info(f"User {user_id} registered for event {event_id}")
        return registration
    
    @staticmethod
    def cancel_registration(registration_id, user_id):
        """
        Cancel event registration
        
        Args:
            registration_id: Registration ID
            user_id: User ID (for authorization)
            
        Returns:
            bool: True if successful
            
        Raises:
            ValueError: If registration not found
            PermissionError: If user doesn't own the registration
        """
        registration = EventRegistration.query.get(registration_id)
        if not registration:
            raise ValueError("Registration not found")
        
        if registration.user_id != user_id:
            raise PermissionError("You are not authorized to cancel this registration")
        
        registration.status = 'cancelled'
        registration.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        
        logger.info(f"Registration cancelled: {registration_id}")
        return True
    
    @staticmethod
    def get_event_by_id(event_id):
        """Get event by ID"""
        return Event.query.get(event_id)
    
    @staticmethod
    def get_upcoming_events(limit=50, offset=0, filters=None):
        """
        Get upcoming events
        
        Args:
            limit: Maximum number of events to return
            offset: Number of events to skip (for pagination)
            filters: Optional dictionary of filters (category, location, etc.)
            
        Returns:
            list: List of upcoming events
        """
        query = Event.query.filter_by(status='upcoming')
        
        # Apply filters if provided
        if filters:
            if 'category' in filters:
                query = query.filter_by(category=filters['category'])
            
            if 'location' in filters:
                query = query.filter(Event.location.ilike(f"%{filters['location']}%"))
            
            if 'start_date' in filters:
                query = query.filter(Event.event_date >= filters['start_date'])
            
            if 'end_date' in filters:
                query = query.filter(Event.event_date <= filters['end_date'])
        
        events = query.order_by(Event.event_date.asc()).offset(offset).limit(limit).all()
        
        return events
    
    @staticmethod
    def get_events_by_organizer(organizer_id):
        """Get all events created by a user"""
        return Event.query.filter_by(organizer_id=organizer_id).order_by(
            Event.event_date.desc()
        ).all()
    
    @staticmethod
    def get_user_registrations(user_id, status=None):
        """
        Get all event registrations for a user
        
        Args:
            user_id: User ID
            status: Optional filter by status
            
        Returns:
            list: List of registrations
        """
        query = EventRegistration.query.filter_by(user_id=user_id)
        
        if status:
            query = query.filter_by(status=status)
        
        registrations = query.order_by(EventRegistration.created_at.desc()).all()
        
        return registrations
    
    @staticmethod
    def get_event_attendees(event_id, organizer_id):
        """
        Get list of attendees for an event
        
        Args:
            event_id: Event ID
            organizer_id: Organizer ID (for authorization)
            
        Returns:
            list: List of registrations
            
        Raises:
            PermissionError: If user is not the organizer
        """
        event = Event.query.get(event_id)
        if not event:
            raise ValueError("Event not found")
        
        if event.organizer_id != organizer_id:
            raise PermissionError("You are not authorized to view attendees")
        
        registrations = EventRegistration.query.filter_by(
            event_id=event_id,
            status='confirmed'
        ).all()
        
        return registrations
    
    @staticmethod
    def search_events(search_query, limit=20):
        """
        Search events by title, description, or location
        
        Args:
            search_query: Search string
            limit: Maximum results to return
            
        Returns:
            list: List of matching events
        """
        pattern = f"%{search_query}%"
        events = Event.query.filter(
            db.or_(
                Event.title.ilike(pattern),
                Event.description.ilike(pattern),
                Event.location.ilike(pattern)
            )
        ).filter_by(status='upcoming').limit(limit).all()
        
        return events
    
    @staticmethod
    def get_event_statistics(event_id, organizer_id):
        """
        Get statistics for an event
        
        Args:
            event_id: Event ID
            organizer_id: Organizer ID (for authorization)
            
        Returns:
            dict: Event statistics
        """
        event = Event.query.get(event_id)
        if not event:
            raise ValueError("Event not found")
        
        if event.organizer_id != organizer_id:
            raise PermissionError("You are not authorized to view statistics")
        
        confirmed_count = EventRegistration.query.filter_by(
            event_id=event_id,
            status='confirmed'
        ).count()
        
        cancelled_count = EventRegistration.query.filter_by(
            event_id=event_id,
            status='cancelled'
        ).count()
        
        return {
            'total_confirmed': confirmed_count,
            'total_cancelled': cancelled_count,
            'spots_remaining': event.max_attendees - confirmed_count if event.max_attendees else None,
            'is_full': event.max_attendees and confirmed_count >= event.max_attendees
        }
