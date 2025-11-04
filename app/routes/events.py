# /app/routes/events.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from datetime import datetime, timedelta

from app import db
from app.models.event import Event
from app.models.event_registration import EventRegistration
from app.models.user import User
from app.models.dog import Dog
from app.utils.sanitizer import sanitize_event_input
from app.schemas.event_schemas import (
    EventCreateSchema, EventUpdateSchema, EventResponseSchema, EventListSchema
)
from app.schemas.event_registration_schemas import (
    EventRegistrationCreateSchema, EventRegistrationResponseSchema
)

# Create Blueprint
events_bp = Blueprint('events', __name__)

@events_bp.route('/', methods=['POST'], strict_slashes=False)
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

        if not (user.is_shelter() or user.is_admin()):
            return jsonify({'error': 'Only shelters and admins can create events'}), 403

        schema = EventCreateSchema()
        data = schema.load(request.json)
        
        # Sanitize text fields to prevent XSS attacks
        data = sanitize_event_input(data)

        event_date = data['event_date']
        registration_deadline = data.get('registration_deadline')
        if registration_deadline and registration_deadline >= event_date:
            return jsonify({
                'error': 'Validation failed',
                'messages': {
                    'registration_deadline': ['Registration deadline must be before the event date.']
                }
            }), 400

        event_kwargs = {
            'description': data.get('description'),
            'category': data.get('category'),
            'duration_hours': data.get('duration_hours'),
            'registration_deadline': registration_deadline,
            'city': data.get('city'),
            'country': data.get('country'),
            'venue_details': data.get('venue_details'),
            'max_participants': data.get('max_participants'),
            'price': data.get('price'),
            'currency': data.get('currency'),
            'min_age_requirement': data.get('min_age_requirement'),
            'max_age_requirement': data.get('max_age_requirement'),
            'vaccination_required': data.get('vaccination_required'),
            'special_requirements': data.get('special_requirements'),
            'requires_approval': data.get('requires_approval'),
            'contact_email': data.get('contact_email'),
            'contact_phone': data.get('contact_phone'),
            'additional_info': data.get('additional_info'),
            'rules_and_guidelines': data.get('rules_and_guidelines'),
            'image_url': data.get('image_url')
        }

        event = Event(
            organizer_id=current_user_id,
            title=data['title'],
            event_date=event_date,
            location=data['location'],
            status='published',  # Auto-publish events for now
            **{k: v for k, v in event_kwargs.items() if v is not None}
        )

        if data.get('size_requirements') is not None:
            event.set_size_requirements_list(data['size_requirements'])

        if data.get('breed_restrictions') is not None:
            event.set_breed_restrictions_list(data['breed_restrictions'])

        db.session.add(event)
        db.session.commit()

        return jsonify({
            'message': 'Event created successfully',
            'event': event.to_dict(include_organizer=True)
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


@events_bp.route('/', methods=['GET'], strict_slashes=False)
def get_events():
    """
    Get events with optional filters
    GET /api/events?category=adoption&city=Merida&upcoming_only=true
    """
    try:
        schema = EventListSchema()
        filters = schema.load(request.args)

        query = Event.query

        status = filters.get('status')
        if status:
            query = query.filter(Event.status == status)
        else:
            query = query.filter(Event.status == 'published')

        category = filters.get('category')
        if category:
            query = query.filter(Event.category == category)

        city = filters.get('city')
        if city:
            like_pattern = f"%{city}%"
            query = query.filter(
                db.or_(
                    Event.city.ilike(like_pattern),
                    Event.location.ilike(like_pattern)
                )
            )

        country = filters.get('country')
        if country:
            query = query.filter(Event.country.ilike(f"%{country}%"))

        if filters.get('upcoming_only', True):
            query = query.filter(Event.event_date >= datetime.utcnow())

        if filters.get('registration_open_only'):
            now = datetime.utcnow()
            query = query.filter(
                db.or_(
                    Event.registration_deadline.is_(None),
                    Event.registration_deadline >= now
                )
            )

        if filters.get('price_max') is not None:
            query = query.filter(Event.price <= filters['price_max'])

        if filters.get('free_only'):
            query = query.filter(Event.price == 0)

        organizer_type = filters.get('organizer_type')
        if organizer_type:
            query = query.join(User)
            if organizer_type == 'shelter':
                query = query.filter(User.user_type == 'shelter')
            elif organizer_type == 'admin':
                query = query.filter(User.user_type == 'admin')

        start_date = filters.get('start_date')
        if start_date:
            query = query.filter(Event.event_date >= start_date)

        end_date = filters.get('end_date')
        if end_date:
            query = query.filter(Event.event_date <= end_date)

        sort_by = request.args.get('sort_by', 'date')
        if sort_by == 'date':
            query = query.order_by(Event.event_date.asc())
        elif sort_by == 'created':
            query = query.order_by(Event.created_at.desc())
        elif sort_by == 'popularity':
            query = query.order_by(Event.current_participants.desc())

        limit = filters.get('limit', 20)
        offset = filters.get('offset', 0)
        events = query.limit(limit).offset(offset).all()

        # Get current user ID if authenticated
        current_user_id = None
        try:
            from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
            verify_jwt_in_request(optional=True)
            current_user_id = get_jwt_identity()
            if current_user_id:
                current_user_id = int(current_user_id)
        except:
            pass  # User not authenticated
        
        events_data = [event.to_dict(include_organizer=True, current_user_id=current_user_id) for event in events]

        filters_response = dict(filters)
        if not status:
            filters_response['status'] = 'published'
        filters_response['sort_by'] = sort_by

        return jsonify({
            'events': events_data,
            'count': len(events_data),
            'limit': limit,
            'offset': offset,
            'filters_applied': filters_response
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

        if not event.can_be_edited_by(current_user_id):
            return jsonify({'error': 'You can only edit your own events'}), 403

        schema = EventUpdateSchema()
        data = schema.load(request.json)
        
        # Sanitize text fields to prevent XSS attacks
        data = sanitize_event_input(data)

        proposed_event_date = data.get('event_date') or event.event_date
        proposed_deadline = data.get('registration_deadline') or event.registration_deadline
        if proposed_deadline and proposed_event_date and proposed_deadline >= proposed_event_date:
            return jsonify({
                'error': 'Validation failed',
                'messages': {
                    'registration_deadline': ['Registration deadline must be before the event date.']
                }
            }), 400

        for field, value in data.items():
            if field == 'size_requirements':
                event.set_size_requirements_list(value)
                continue
            if field == 'breed_restrictions':
                event.set_breed_restrictions_list(value)
                continue
            if hasattr(event, field):
                setattr(event, field, value)

        event.updated_at = datetime.utcnow()

        db.session.commit()

        return jsonify({
            'message': 'Event updated successfully',
            'event': event.to_dict(include_organizer=True)
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
        
        # Only admins can delete/cancel events
        if not user.is_admin():
            return jsonify({'error': 'Admin privileges required to cancel events'}), 403
        
        # Soft delete - mark as cancelled instead of hard delete
        event.status = 'cancelled'
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
        
        # Check if user is already registered (only active registrations)
        existing_registration = EventRegistration.query.filter(
            EventRegistration.event_id == event_id,
            EventRegistration.user_id == current_user_id,
            EventRegistration.status.in_(['confirmed', 'pending'])
        ).first()
        
        if existing_registration:
            # Make registration idempotent for clients: return the existing registration
            return jsonify({
                'message': 'You are already registered for this event',
                'registration': existing_registration.to_dict(include_event=False, include_user=True)
            }), 200
        
        # Check if user has a cancelled registration that we can reactivate
        cancelled_registration = EventRegistration.query.filter(
            EventRegistration.event_id == event_id,
            EventRegistration.user_id == current_user_id,
            EventRegistration.status == 'cancelled'
        ).first()
        
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
            
            can_participate, requirement_message = event.can_dog_participate(dog)
            if not can_participate:
                return jsonify({'error': requirement_message}), 400
        
        # Either reactivate cancelled registration or create new one
        if cancelled_registration:
            # Reactivate cancelled registration
            registration = cancelled_registration
            registration.notes = data.get('notes', '')
            registration.special_requests = data.get('special_requests', '')
            registration.emergency_contact_name = data.get('emergency_contact_name', '')
            registration.emergency_contact_phone = data.get('emergency_contact_phone', '')
            registration.cancelled_at = None
        else:
            # Create new registration
            registration = EventRegistration(
                event_id=event_id,
                user_id=current_user_id,
                dog_id=dog_id,
                notes=data.get('notes'),
                special_requests=data.get('special_requests'),
                emergency_contact_name=data.get('emergency_contact_name'),
                emergency_contact_phone=data.get('emergency_contact_phone')
            )
            db.session.add(registration)
        
        # Set status based on event requirements
        if event.requires_approval:
            registration.status = 'pending'
        else:
            registration.status = 'confirmed'
        
        # Handle payment if event has a price
        if event.price > 0:
            registration.payment_status = 'pending'
            # TODO: Integrate with payment processor
        else:
            registration.payment_status = 'completed'
        
        # Update event stats
        event.update_participant_count()
        
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
            EventRegistration.user_id == current_user_id,
            EventRegistration.status.in_(['confirmed', 'pending'])
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
            event.update_participant_count()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Successfully unregistered from event',
            'registration': registration.to_dict(include_event=False, include_user=True)
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


@events_bp.route('/my-events', methods=['GET'], strict_slashes=False)
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
        events_data = [event.to_dict(include_organizer=False) for event in events]
        
        return jsonify({
            'events': events_data,
            'count': len(events_data)
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to get your events',
            'message': str(e)
        }), 500


@events_bp.route('/my-registrations', methods=['GET'], strict_slashes=False)
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


@events_bp.route('/categories', methods=['GET'], strict_slashes=False)
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

        total_events = Event.query.count()
        active_events = Event.query.filter(Event.status == 'published').count()
        upcoming_events = Event.query.filter(
            Event.event_date >= datetime.utcnow(),
            Event.status == 'published'
        ).count()

        total_registrations = EventRegistration.query.count()
        confirmed_registrations = EventRegistration.query.filter(
            EventRegistration.status == 'confirmed'
        ).count()

        categories_stats = db.session.query(
            Event.category,
            db.func.count(Event.id).label('count')
        ).group_by(Event.category).all()

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
                'by_type': [{'type': cat[0], 'count': cat[1]} for cat in categories_stats]
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


