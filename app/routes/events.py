# /app/routes/events.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from datetime import datetime, timedelta

from app import db
from app.models import (
    Event, EventRegistration, User, Dog,
    EventCreateSchema, EventUpdateSchema, EventResponseSchema, EventListSchema,
    EventRegistrationCreateSchema, EventRegistrationResponseSchema
)

# Create Blueprint
events_bp = Blueprint('events', __name__)

@events_bp.route('/', methods=['POST'])
@jwt_required()
def create_event():
    """
    Create a new event
    POST /api/events
    """
    try:
        current_user_id = int(get_jwt_identity())
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Check if user can create events (shelters and admins)
        if not (user.is_shelter() or user.is_admin()):
            return jsonify({'error': 'Only shelters and admins can create events'}), 403
        
        # Validate input data
        schema = EventCreateSchema()
        data = schema.load(request.json)
        
        # Create new event
        event = Event(
            organizer_id=current_user_id,
            title=data['title'],
            description=data['description'],
            event_date=data['event_date'],
            location=data['location'],
            event_type=data.get('event_type', 'meetup'),
            price=data.get('price', 0.0),
            max_participants=data.get('max_participants'),
            requires_approval=data.get('requires_approval', False),
            allows_dogs=data.get('allows_dogs', True),
            latitude=data.get('latitude'),
            longitude=data.get('longitude'),
            image_url=data.get('image_url'),
            requirements=data.get('requirements'),
            contact_info=data.get('contact_info')
        )
        
        # Save to database
        db.session.add(event)
        db.session.commit()
        
        return jsonify({
            'message': 'Event created successfully',
            'event': event.to_dict(include_organizer=True, include_stats=True)
        }), 201
        
    except ValidationError as e:
        return jsonify({
            'error': 'Validation failed',
            'messages': e.messages
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'Failed to create event',
            'message': str(e)
        }), 500


@events_bp.route('/', methods=['GET'])
def get_events():
    """
    Get events with optional filters
    GET /api/events?event_type=adoption&city=Mérida&upcoming=true
    """
    try:
        # Validate query parameters
        schema = EventListSchema()
        filters = schema.load(request.args)
        
        # Build base query
        query = Event.query.filter(Event.is_active == True)
        
        # Apply filters
        if filters.get('event_type'):
            query = query.filter(Event.event_type == filters['event_type'])
        
        if filters.get('city'):
            query = query.filter(Event.location.ilike(f"%{filters['city']}%"))
        
        if filters.get('upcoming', True):
            query = query.filter(Event.event_date >= datetime.utcnow())
        
        if filters.get('free_only', False):
            query = query.filter(Event.price == 0)
        
        if filters.get('organizer_type'):
            if filters['organizer_type'] == 'shelter':
                query = query.join(User).filter(User.user_type == 'shelter')
            elif filters['organizer_type'] == 'admin':
                query = query.join(User).filter(User.user_type == 'admin')
        
        # Date range filtering
        if filters.get('start_date'):
            query = query.filter(Event.event_date >= filters['start_date'])
        
        if filters.get('end_date'):
            query = query.filter(Event.event_date <= filters['end_date'])
        
        # Distance filtering (if coordinates provided)
        user_lat = filters.get('user_latitude')
        user_lng = filters.get('user_longitude')
        max_distance = filters.get('max_distance_km')
        
        if user_lat and user_lng and max_distance:
            # Note: This is a simplified distance calculation
            # In production, you'd want to use a proper spatial database function
            pass  # TODO: Implement proper geospatial filtering
        
        # Apply sorting
        sort_by = filters.get('sort_by', 'date')
        if sort_by == 'date':
            query = query.order_by(Event.event_date.asc())
        elif sort_by == 'created':
            query = query.order_by(Event.created_at.desc())
        elif sort_by == 'popularity':
            query = query.order_by(Event.registered_count.desc())
        
        # Apply pagination
        limit = filters.get('limit', 20)
        offset = filters.get('offset', 0)
        events = query.limit(limit).offset(offset).all()
        
        # Convert to dict
        events_data = [event.to_dict(include_organizer=True, include_stats=True) for event in events]
        
        return jsonify({
            'events': events_data,
            'count': len(events_data),
            'limit': limit,
            'offset': offset,
            'filters_applied': filters
        }), 200
        
    except ValidationError as e:
        return jsonify({
            'error': 'Validation failed',
            'messages': e.messages
        }), 400
    except Exception as e:
        return jsonify({
            'error': 'Failed to get events',
            'message': str(e)
        }), 500


@events_bp.route('/<int:event_id>', methods=['GET'])
def get_event(event_id):
    """
    Get specific event details
    GET /api/events/123
    """
    try:
        event = Event.query.get(event_id)
        
        if not event:
            return jsonify({'error': 'Event not found'}), 404
        
        # Increment view count
        event.increment_view_count()
        
        # Get current user if authenticated (for registration status)
        current_user_id = None
        try:
            from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
            verify_jwt_in_request(optional=True)
            current_user_id = int(get_jwt_identity()) if get_jwt_identity() else None
        except:
            pass
        
        event_data = event.to_dict(
            include_organizer=True, 
            current_user_id=current_user_id
        )
        
        return jsonify({
            'event': event_data
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to get event',
            'message': str(e)
        }), 500


@events_bp.route('/<int:event_id>', methods=['PUT'])
@jwt_required()
def update_event(event_id):
    """
    Update event details
    PUT /api/events/123
    """
    try:
        current_user_id = int(get_jwt_identity())
        event = Event.query.get(event_id)
        
        if not event:
            return jsonify({'error': 'Event not found'}), 404
        
        # Check if user can edit this event
        if not event.can_be_edited_by(current_user_id):
            return jsonify({'error': 'You can only edit your own events'}), 403
        
        # Validate input data
        schema = EventUpdateSchema()
        data = schema.load(request.json)
        
        # Update fields
        for field, value in data.items():
            if hasattr(event, field):
                setattr(event, field, value)
        
        # Update timestamp
        event.updated_at = datetime.utcnow()
        
        # Save changes
        db.session.commit()
        
        return jsonify({
            'message': 'Event updated successfully',
            'event': event.to_dict(include_organizer=True, include_stats=True)
        }), 200
        
    except ValidationError as e:
        return jsonify({
            'error': 'Validation failed',
            'messages': e.messages
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'Failed to update event',
            'message': str(e)
        }), 500


@events_bp.route('/<int:event_id>', methods=['DELETE'])
@jwt_required()
def delete_event(event_id):
    """
    Delete/cancel event
    DELETE /api/events/123
    """
    try:
        current_user_id = int(get_jwt_identity())
        user = User.query.get(current_user_id)
        event = Event.query.get(event_id)
        
        if not event:
            return jsonify({'error': 'Event not found'}), 404
        
        # Check if user can delete this event (organizer or admin)
        if event.organizer_id != current_user_id and not user.is_admin():
            return jsonify({'error': 'You can only delete your own events'}), 403
        
        # Soft delete - mark as cancelled instead of hard delete
        event.status = 'cancelled'
        event.is_active = False
        event.updated_at = datetime.utcnow()
        
        # Notify all registered participants
        # TODO: Implement notification system
        
        db.session.commit()
        
        return jsonify({
            'message': 'Event cancelled successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'Failed to cancel event',
            'message': str(e)
        }), 500


# Event Registration Endpoints
@events_bp.route('/<int:event_id>/register', methods=['POST'])
@jwt_required()
def register_for_event(event_id):
    """
    Register for an event
    POST /api/events/123/register
    """
    try:
        current_user_id = int(get_jwt_identity())
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        event = Event.query.get(event_id)
        if not event:
            return jsonify({'error': 'Event not found'}), 404
        
        # Check if event is still accepting registrations
        if not event.is_registration_open():
            return jsonify({'error': 'Registration is not open for this event'}), 400
        
        # Check if user is already registered
        existing_registration = EventRegistration.query.filter(
            EventRegistration.event_id == event_id,
            EventRegistration.user_id == current_user_id
        ).first()
        
        if existing_registration:
            return jsonify({'error': 'You are already registered for this event'}), 400
        
        # Validate input data
        schema = EventRegistrationCreateSchema()
        data = schema.load(request.json)
        
        # Get dog if specified
        dog_id = data.get('dog_id')
        dog = None
        if dog_id:
            dog = Dog.query.filter(
                Dog.id == dog_id,
                Dog.owner_id == current_user_id
            ).first()
            
            if not dog:
                return jsonify({'error': 'Dog not found or not owned by you'}), 404
            
            if not event.allows_dogs:
                return jsonify({'error': 'This event does not allow dogs'}), 400
        
        # Create registration
        registration = EventRegistration(
            event_id=event_id,
            user_id=current_user_id,
            dog_id=dog_id,
            registration_notes=data.get('registration_notes'),
            emergency_contact=data.get('emergency_contact'),
            dietary_restrictions=data.get('dietary_restrictions')
        )
        
        # Set status based on event requirements
        if event.requires_approval:
            registration.status = 'pending'
        else:
            registration.status = 'confirmed'
            registration.confirmed_at = datetime.utcnow()
        
        # Handle payment if event has a price
        if event.price > 0:
            registration.payment_status = 'pending'
            # TODO: Integrate with payment processor
        else:
            registration.payment_status = 'completed'
        
        # Save registration
        db.session.add(registration)
        
        # Update event stats
        event.update_registration_stats()
        
        db.session.commit()
        
        response_message = 'Successfully registered for event'
        if event.requires_approval:
            response_message += ' (pending organizer approval)'
        
        return jsonify({
            'message': response_message,
            'registration': registration.to_dict(include_event=False, include_user=True)
        }), 201
        
    except ValidationError as e:
        return jsonify({
            'error': 'Validation failed',
            'messages': e.messages
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'Failed to register for event',
            'message': str(e)
        }), 500


@events_bp.route('/<int:event_id>/unregister', methods=['DELETE'])
@jwt_required()
def unregister_from_event(event_id):
    """
    Unregister from an event
    DELETE /api/events/123/unregister
    """
    try:
        current_user_id = int(get_jwt_identity())
        
        registration = EventRegistration.query.filter(
            EventRegistration.event_id == event_id,
            EventRegistration.user_id == current_user_id
        ).first()
        
        if not registration:
            return jsonify({'error': 'You are not registered for this event'}), 404
        
        event = Event.query.get(event_id)
        
        # Check if it's too late to unregister
        if event and event.event_date:
            hours_until_event = (event.event_date - datetime.utcnow()).total_seconds() / 3600
            if hours_until_event < 24:  # 24 hour cancellation policy
                return jsonify({
                    'error': 'Cannot unregister less than 24 hours before the event'
                }), 400
        
        # Handle refund if payment was made
        if registration.payment_status == 'completed' and event.price > 0:
            # TODO: Process refund
            registration.payment_status = 'refunded'
        
        # Cancel registration
        registration.status = 'cancelled'
        registration.cancelled_at = datetime.utcnow()
        
        # Update event stats
        if event:
            event.update_registration_stats()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Successfully unregistered from event'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'Failed to unregister from event',
            'message': str(e)
        }), 500


@events_bp.route('/<int:event_id>/registrations', methods=['GET'])
@jwt_required()
def get_event_registrations(event_id):
    """
    Get registrations for an event (organizers and admins only)
    GET /api/events/123/registrations
    """
    try:
        current_user_id = int(get_jwt_identity())
        user = User.query.get(current_user_id)
        event = Event.query.get(event_id)
        
        if not event:
            return jsonify({'error': 'Event not found'}), 404
        
        # Check if user can view registrations
        if event.organizer_id != current_user_id and not user.is_admin():
            return jsonify({'error': 'Only event organizers can view registrations'}), 403
        
        # Get query parameters
        status = request.args.get('status')  # pending, confirmed, cancelled
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        # Build query
        query = EventRegistration.query.filter(EventRegistration.event_id == event_id)
        
        if status:
            query = query.filter(EventRegistration.status == status)
        
        # Get registrations
        registrations = query.order_by(EventRegistration.created_at.desc())\
                            .limit(limit).offset(offset).all()
        
        # Convert to dict
        registrations_data = [
            reg.to_dict(include_event=False, include_user=True) 
            for reg in registrations
        ]
        
        return jsonify({
            'registrations': registrations_data,
            'count': len(registrations_data),
            'event_id': event_id,
            'limit': limit,
            'offset': offset
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to get event registrations',
            'message': str(e)
        }), 500


@events_bp.route('/my-events', methods=['GET'])
@jwt_required()
def get_my_events():
    """
    Get events organized by current user
    GET /api/events/my-events
    """
    try:
        current_user_id = int(get_jwt_identity())
        
        # Get user's organized events
        events = Event.query.filter(Event.organizer_id == current_user_id)\
                           .order_by(Event.event_date.desc()).all()
        
        # Convert to dict
        events_data = [event.to_dict(include_organizer=False, include_stats=True) for event in events]
        
        return jsonify({
            'events': events_data,
            'count': len(events_data)
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to get your events',
            'message': str(e)
        }), 500


@events_bp.route('/my-registrations', methods=['GET'])
@jwt_required()
def get_my_registrations():
    """
    Get events user is registered for
    GET /api/events/my-registrations
    """
    try:
        current_user_id = int(get_jwt_identity())
        
        # Get query parameters
        status = request.args.get('status')  # pending, confirmed, cancelled
        upcoming_only = request.args.get('upcoming_only', 'true').lower() == 'true'
        
        # Build query
        query = EventRegistration.query.filter(EventRegistration.user_id == current_user_id)
        
        if status:
            query = query.filter(EventRegistration.status == status)
        
        if upcoming_only:
            query = query.join(Event).filter(Event.event_date >= datetime.utcnow())
        
        # Get registrations
        registrations = query.order_by(EventRegistration.created_at.desc()).all()
        
        # Convert to dict
        registrations_data = [
            reg.to_dict(include_event=True, include_user=False) 
            for reg in registrations
        ]
        
        return jsonify({
            'registrations': registrations_data,
            'count': len(registrations_data)
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to get your registrations',
            'message': str(e)
        }), 500


# Admin/Organizer specific endpoints
@events_bp.route('/<int:event_id>/registrations/<int:registration_id>/approve', methods=['PUT'])
@jwt_required()
def approve_registration(event_id, registration_id):
    """
    Approve a pending registration
    PUT /api/events/123/registrations/456/approve
    """
    try:
        current_user_id = int(get_jwt_identity())
        user = User.query.get(current_user_id)
        
        registration = EventRegistration.query.get(registration_id)
        if not registration or registration.event_id != event_id:
            return jsonify({'error': 'Registration not found'}), 404
        
        event = registration.event
        
        # Check permissions
        if event.organizer_id != current_user_id and not user.is_admin():
            return jsonify({'error': 'Only event organizers can approve registrations'}), 403
        
        # Approve registration
        registration.approve_registration(current_user_id)
        
        return jsonify({
            'message': 'Registration approved successfully',
            'registration': registration.to_dict(include_event=False, include_user=True)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'Failed to approve registration',
            'message': str(e)
        }), 500


@events_bp.route('/<int:event_id>/registrations/<int:registration_id>/reject', methods=['PUT'])
@jwt_required()
def reject_registration(event_id, registration_id):
    """
    Reject a pending registration
    PUT /api/events/123/registrations/456/reject
    """
    try:
        current_user_id = int(get_jwt_identity())
        user = User.query.get(current_user_id)
        
        registration = EventRegistration.query.get(registration_id)
        if not registration or registration.event_id != event_id:
            return jsonify({'error': 'Registration not found'}), 404
        
        event = registration.event
        
        # Check permissions
        if event.organizer_id != current_user_id and not user.is_admin():
            return jsonify({'error': 'Only event organizers can reject registrations'}), 403
        
        # Get rejection reason
        data = request.json or {}
        rejection_reason = data.get('rejection_reason', 'No reason provided')
        
        # Reject registration
        registration.reject_registration(current_user_id, rejection_reason)
        
        return jsonify({
            'message': 'Registration rejected successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'Failed to reject registration',
            'message': str(e)
        }), 500


@events_bp.route('/categories', methods=['GET'])
def get_event_categories():
    """
    Get available event types and categories
    GET /api/events/categories
    """
    try:
        categories = {
            'event_types': [
                {'value': 'meetup', 'label': 'Dog Meetup'},
                {'value': 'training', 'label': 'Training Workshop'},
                {'value': 'adoption', 'label': 'Adoption Fair'},
                {'value': 'competition', 'label': 'Dog Competition'},
                {'value': 'health', 'label': 'Health & Wellness'},
                {'value': 'social', 'label': 'Social Event'},
                {'value': 'educational', 'label': 'Educational Workshop'},
                {'value': 'fundraiser', 'label': 'Fundraising Event'}
            ],
            'statuses': [
                {'value': 'draft', 'label': 'Draft'},
                {'value': 'published', 'label': 'Published'},
                {'value': 'ongoing', 'label': 'Ongoing'},
                {'value': 'completed', 'label': 'Completed'},
                {'value': 'cancelled', 'label': 'Cancelled'}
            ],
            'registration_statuses': [
                {'value': 'pending', 'label': 'Pending Approval'},
                {'value': 'confirmed', 'label': 'Confirmed'},
                {'value': 'cancelled', 'label': 'Cancelled'},
                {'value': 'rejected', 'label': 'Rejected'}
            ]
        }
        
        return jsonify(categories), 200
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to get event categories',
            'message': str(e)
        }), 500


@events_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_event_stats():
    """
    Get event statistics (admin only)
    GET /api/events/stats
    """
    try:
        current_user_id = int(get_jwt_identity())
        user = User.query.get(current_user_id)
        
        if not user or not user.is_admin():
            return jsonify({'error': 'Admin privileges required'}), 403
        
        # Calculate event statistics
        total_events = Event.query.count()
        active_events = Event.query.filter(Event.is_active == True).count()
        upcoming_events = Event.query.filter(
            Event.event_date >= datetime.utcnow(),
            Event.is_active == True
        ).count()
        
        # Registration statistics
        total_registrations = EventRegistration.query.count()
        confirmed_registrations = EventRegistration.query.filter(
            EventRegistration.status == 'confirmed'
        ).count()
        
        # Event type breakdown
        event_types_stats = db.session.query(
            Event.event_type,
            db.func.count(Event.id).label('count')
        ).group_by(Event.event_type).all()
        
        # Recent activity (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        new_events_30d = Event.query.filter(Event.created_at >= thirty_days_ago).count()
        new_registrations_30d = EventRegistration.query.filter(
            EventRegistration.created_at >= thirty_days_ago
        ).count()
        
        stats = {
            'events': {
                'total': total_events,
                'active': active_events,
                'upcoming': upcoming_events,
                'new_last_30_days': new_events_30d,
                'by_type': [{'type': et[0], 'count': et[1]} for et in event_types_stats]
            },
            'registrations': {
                'total': total_registrations,
                'confirmed': confirmed_registrations,
                'pending': total_registrations - confirmed_registrations,
                'new_last_30_days': new_registrations_30d
            }
        }
        
        return jsonify({
            'stats': stats,
            'generated_at': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to get event stats',
            'message': str(e)
        }), 500