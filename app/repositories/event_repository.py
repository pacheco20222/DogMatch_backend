"""
Event Repository

Handles all database operations for Event and EventRegistration models.
Provides methods for querying, creating, updating, and deleting events.
"""

from app import db
from app.models.event import Event
from app.models.event_registration import EventRegistration
from app.models.user import User
from app.models.dog import Dog
from sqlalchemy import or_, and_
from sqlalchemy.orm import joinedload, selectinload
from datetime import datetime, timezone


class EventRepository:
    """Repository for Event model data access"""
    
    @staticmethod
    def find_by_id(event_id):
        """
        Find event by ID
        
        Args:
            event_id: Event ID
            
        Returns:
            Event or None
        """
        return Event.query.get(event_id)
    
    @staticmethod
    def find_by_organizer(organizer_id):
        """
        Find all events created by an organizer
        
        Args:
            organizer_id: User ID of organizer
            
        Returns:
            list: List of events
        """
        return Event.query.filter_by(organizer_id=organizer_id).order_by(
            Event.event_date.desc()
        ).all()
    
    @staticmethod
    def create(event_data):
        """
        Create a new event
        
        Args:
            event_data: Dictionary of event attributes
            
        Returns:
            Event: Created event object
        """
        event = Event(**event_data)
        db.session.add(event)
        db.session.commit()
        db.session.refresh(event)
        return event
    
    @staticmethod
    def update(event, updates):
        """
        Update event attributes
        
        Args:
            event: Event object to update
            updates: Dictionary of fields to update
            
        Returns:
            Event: Updated event object
        """
        for key, value in updates.items():
            if hasattr(event, key):
                setattr(event, key, value)
        
        event.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        db.session.refresh(event)
        return event
    
    @staticmethod
    def delete(event):
        """
        Delete an event
        
        Args:
            event: Event object to delete
            
        Returns:
            bool: True if successful
        """
        db.session.delete(event)
        db.session.commit()
        return True
    
    @staticmethod
    def find_upcoming(limit=50, offset=0):
        """
        Find all upcoming events
        
        Args:
            limit: Maximum results to return
            offset: Number of results to skip
            
        Returns:
            list: List of upcoming events
        """
        return Event.query.filter_by(status='upcoming').order_by(
            Event.event_date.asc()
        ).limit(limit).offset(offset).all()
    
    @staticmethod
    def find_by_status(status, limit=50, offset=0):
        """
        Find events by status
        
        Args:
            status: Event status (upcoming, completed, cancelled)
            limit: Maximum results to return
            offset: Number of results to skip
            
        Returns:
            list: List of events
        """
        return Event.query.filter_by(status=status).order_by(
            Event.event_date.desc()
        ).limit(limit).offset(offset).all()
    
    @staticmethod
    def find_by_category(category, limit=50):
        """
        Find events by category
        
        Args:
            category: Event category
            limit: Maximum results to return
            
        Returns:
            list: List of events
        """
        return Event.query.filter_by(
            category=category,
            status='upcoming'
        ).order_by(Event.event_date.asc()).limit(limit).all()
    
    @staticmethod
    def find_by_location(location, limit=50):
        """
        Find events by location
        
        Args:
            location: Location string
            limit: Maximum results to return
            
        Returns:
            list: List of events
        """
        return Event.query.filter(
            Event.location.ilike(f"%{location}%")
        ).filter_by(status='upcoming').order_by(
            Event.event_date.asc()
        ).limit(limit).all()
    
    @staticmethod
    def find_by_date_range(start_date, end_date, limit=100):
        """
        Find events within a date range
        
        Args:
            start_date: Start date
            end_date: End date
            limit: Maximum results to return
            
        Returns:
            list: List of events
        """
        return Event.query.filter(
            and_(
                Event.event_date >= start_date,
                Event.event_date <= end_date,
                Event.status == 'upcoming'
            )
        ).order_by(Event.event_date.asc()).limit(limit).all()
    
    @staticmethod
    def search(query, limit=20):
        """
        Search events by title, description, or location
        
        Args:
            query: Search string
            limit: Maximum results to return
            
        Returns:
            list: List of matching events
        """
        pattern = f"%{query}%"
        return Event.query.filter(
            or_(
                Event.title.ilike(pattern),
                Event.description.ilike(pattern),
                Event.location.ilike(pattern)
            )
        ).filter_by(status='upcoming').limit(limit).all()
    
    @staticmethod
    def find_by_filters(filters, limit=50, offset=0):
        """
        Find events with advanced filters
        
        Args:
            filters: Dictionary of filter criteria
            limit: Maximum results to return
            offset: Number of results to skip
            
        Returns:
            list: List of matching events
        """
        query = Event.query.filter_by(status='upcoming')
        
        if 'category' in filters and filters['category']:
            query = query.filter_by(category=filters['category'])
        
        if 'location' in filters and filters['location']:
            query = query.filter(Event.location.ilike(f"%{filters['location']}%"))
        
        if 'start_date' in filters:
            query = query.filter(Event.event_date >= filters['start_date'])
        
        if 'end_date' in filters:
            query = query.filter(Event.event_date <= filters['end_date'])
        
        if 'organizer_id' in filters:
            query = query.filter_by(organizer_id=filters['organizer_id'])
        
        return query.order_by(Event.event_date.asc()).limit(limit).offset(offset).all()
    
    @staticmethod
    def count_by_organizer(organizer_id):
        """
        Count events created by an organizer
        
        Args:
            organizer_id: User ID
            
        Returns:
            int: Number of events
        """
        return Event.query.filter_by(organizer_id=organizer_id).count()
    
    @staticmethod
    def count_by_status(status):
        """
        Count events by status
        
        Args:
            status: Event status
            
        Returns:
            int: Number of events
        """
        return Event.query.filter_by(status=status).count()
    
    @staticmethod
    def exists(event_id):
        """
        Check if event exists
        
        Args:
            event_id: Event ID
            
        Returns:
            bool: True if exists
        """
        return db.session.query(
            Event.query.filter_by(id=event_id).exists()
        ).scalar()
    
    # ==================== OPTIMIZED METHODS (Prevent N+1 Queries) ====================
    
    @staticmethod
    def find_by_id_with_organizer(event_id):
        """
        Find event by ID with organizer eager loaded (prevents N+1)
        
        Args:
            event_id: Event ID
            
        Returns:
            Event or None with organizer loaded
        """
        return Event.query.options(
            joinedload(Event.organizer)
        ).get(event_id)
    
    @staticmethod
    def find_by_id_with_registrations(event_id):
        """
        Find event by ID with registrations, users, and dogs loaded
        Optimized for event details with attendee list
        
        Args:
            event_id: Event ID
            
        Returns:
            Event or None with all registration details loaded
        """
        return Event.query.options(
            joinedload(Event.organizer),
            selectinload(Event.registrations).joinedload(EventRegistration.user),
            selectinload(Event.registrations).joinedload(EventRegistration.dog)
        ).get(event_id)
    
    @staticmethod
    def find_upcoming_with_organizer(limit=20, offset=0):
        """
        Find upcoming events with organizer loaded
        Optimized for event listing screens
        
        Args:
            limit: Maximum results
            offset: Pagination offset
            
        Returns:
            list: List of events with organizer loaded
        """
        return Event.query.filter(
            and_(
                Event.event_date >= datetime.now(timezone.utc),
                Event.status == 'active'
            )
        ).options(
            joinedload(Event.organizer)
        ).order_by(Event.event_date.asc()).limit(limit).offset(offset).all()
    
    @staticmethod
    def find_by_organizer_with_registration_counts(organizer_id):
        """
        Find events by organizer with registration count
        Optimized for organizer dashboard
        
        Args:
            organizer_id: User ID
            
        Returns:
            list: List of events with registration data loaded
        """
        return Event.query.filter_by(
            organizer_id=organizer_id
        ).options(
            selectinload(Event.registrations)
        ).order_by(Event.event_date.desc()).all()
    
    @staticmethod
    def find_by_category_with_organizer(category, limit=20):
        """
        Find events by category with organizer loaded
        Optimized for category browsing
        
        Args:
            category: Event category
            limit: Maximum results
            
        Returns:
            list: List of events with organizer loaded
        """
        return Event.query.filter(
            and_(
                Event.category == category,
                Event.status == 'active',
                Event.event_date >= datetime.now(timezone.utc)
            )
        ).options(
            joinedload(Event.organizer)
        ).order_by(Event.event_date.asc()).limit(limit).all()
    
    @staticmethod
    def search_with_organizer(search_term, limit=20):
        """
        Search events by title/description with organizer loaded
        Optimized for search results
        
        Args:
            search_term: Search string
            limit: Maximum results
            
        Returns:
            list: List of matching events with organizer
        """
        return Event.query.filter(
            and_(
                Event.status == 'active',
                Event.event_date >= datetime.now(timezone.utc),
                or_(
                    Event.title.ilike(f"%{search_term}%"),
                    Event.description.ilike(f"%{search_term}%")
                )
            )
        ).options(
            joinedload(Event.organizer)
        ).limit(limit).all()


class EventRegistrationRepository:
    """Repository for EventRegistration model data access"""
    
    @staticmethod
    def find_by_id(registration_id):
        """
        Find registration by ID
        
        Args:
            registration_id: Registration ID
            
        Returns:
            EventRegistration or None
        """
        return EventRegistration.query.get(registration_id)
    
    @staticmethod
    def find_by_event(event_id, status=None):
        """
        Find all registrations for an event
        
        Args:
            event_id: Event ID
            status: Optional status filter
            
        Returns:
            list: List of registrations
        """
        query = EventRegistration.query.filter_by(event_id=event_id)
        
        if status:
            query = query.filter_by(status=status)
        
        return query.order_by(EventRegistration.created_at.desc()).all()
    
    @staticmethod
    def find_by_user(user_id, status=None):
        """
        Find all registrations for a user
        
        Args:
            user_id: User ID
            status: Optional status filter
            
        Returns:
            list: List of registrations
        """
        query = EventRegistration.query.filter_by(user_id=user_id)
        
        if status:
            query = query.filter_by(status=status)
        
        return query.order_by(EventRegistration.created_at.desc()).all()
    
    @staticmethod
    def find_by_user_and_event(user_id, event_id):
        """
        Find registration for a specific user and event
        
        Args:
            user_id: User ID
            event_id: Event ID
            
        Returns:
            EventRegistration or None
        """
        return EventRegistration.query.filter_by(
            user_id=user_id,
            event_id=event_id
        ).first()
    
    @staticmethod
    def create(registration_data):
        """
        Create a new registration
        
        Args:
            registration_data: Dictionary of registration attributes
            
        Returns:
            EventRegistration: Created registration object
        """
        registration = EventRegistration(**registration_data)
        db.session.add(registration)
        db.session.commit()
        db.session.refresh(registration)
        return registration
    
    @staticmethod
    def update(registration, updates):
        """
        Update registration attributes
        
        Args:
            registration: EventRegistration object to update
            updates: Dictionary of fields to update
            
        Returns:
            EventRegistration: Updated registration object
        """
        for key, value in updates.items():
            if hasattr(registration, key):
                setattr(registration, key, value)
        
        registration.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        db.session.refresh(registration)
        return registration
    
    @staticmethod
    def delete(registration):
        """
        Delete a registration
        
        Args:
            registration: EventRegistration object to delete
            
        Returns:
            bool: True if successful
        """
        db.session.delete(registration)
        db.session.commit()
        return True
    
    @staticmethod
    def count_by_event(event_id, status=None):
        """
        Count registrations for an event
        
        Args:
            event_id: Event ID
            status: Optional status filter
            
        Returns:
            int: Number of registrations
        """
        query = EventRegistration.query.filter_by(event_id=event_id)
        
        if status:
            query = query.filter_by(status=status)
        
        return query.count()
    
    @staticmethod
    def count_by_user(user_id, status=None):
        """
        Count registrations for a user
        
        Args:
            user_id: User ID
            status: Optional status filter
            
        Returns:
            int: Number of registrations
        """
        query = EventRegistration.query.filter_by(user_id=user_id)
        
        if status:
            query = query.filter_by(status=status)
        
        return query.count()
    
    @staticmethod
    def exists_for_user_and_event(user_id, event_id):
        """
        Check if registration exists for user and event
        
        Args:
            user_id: User ID
            event_id: Event ID
            
        Returns:
            bool: True if exists
        """
        return db.session.query(
            EventRegistration.query.filter_by(
                user_id=user_id,
                event_id=event_id
            ).exists()
        ).scalar()
    
    # ==================== OPTIMIZED METHODS (Prevent N+1 Queries) ====================
    
    @staticmethod
    def find_by_event_with_users_and_dogs(event_id, status=None):
        """
        Find registrations for event with user and dog details loaded
        Optimized for attendee list display
        
        Args:
            event_id: Event ID
            status: Optional status filter
            
        Returns:
            list: List of registrations with relationships loaded
        """
        query = EventRegistration.query.filter_by(
            event_id=event_id
        ).options(
            joinedload(EventRegistration.user),
            joinedload(EventRegistration.dog)
        )
        
        if status:
            query = query.filter_by(status=status)
        
        return query.order_by(EventRegistration.created_at.desc()).all()
    
    @staticmethod
    def find_by_user_with_events(user_id, status=None):
        """
        Find registrations for user with event and organizer loaded
        Optimized for user's event list display
        
        Args:
            user_id: User ID
            status: Optional status filter
            
        Returns:
            list: List of registrations with event details loaded
        """
        query = EventRegistration.query.filter_by(
            user_id=user_id
        ).options(
            joinedload(EventRegistration.event).joinedload(Event.organizer),
            joinedload(EventRegistration.dog)
        )
        
        if status:
            query = query.filter_by(status=status)
        
        return query.order_by(EventRegistration.created_at.desc()).all()
    
    @staticmethod
    def find_by_dog_with_events(dog_id, status=None):
        """
        Find registrations for dog with event and organizer loaded
        Optimized for dog's event history
        
        Args:
            dog_id: Dog ID
            status: Optional status filter
            
        Returns:
            list: List of registrations with event details loaded
        """
        query = EventRegistration.query.filter_by(
            dog_id=dog_id
        ).options(
            joinedload(EventRegistration.event).joinedload(Event.organizer),
            joinedload(EventRegistration.user)
        )
        
        if status:
            query = query.filter_by(status=status)
        
        return query.order_by(EventRegistration.created_at.desc()).all()
