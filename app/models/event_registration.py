# app/models/event_registration.py
from datetime import datetime, timedelta
from app import db
import uuid

class EventRegistration(db.Model):
    """
    EventRegistration model for DogMatch application
    Handles user registrations for events including payments and approvals
    """
    
    # Table configuration
    __tablename__ = 'event_registrations'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Foreign keys
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    dog_id = db.Column(db.Integer, db.ForeignKey('dogs.id'), nullable=True)
    
    # Registration status
    status = db.Column(db.Enum('pending', 'confirmed', 'rejected', 'cancelled', 'waitlisted', name='registration_status_enum'), 
                      nullable=False, default='pending')
    
    # Registration details
    registration_code = db.Column(db.String(20), unique=True, nullable=False)  # Unique ticket code
    notes = db.Column(db.Text, nullable=True)  # User's notes (why they want to attend, etc.)
    special_requests = db.Column(db.Text, nullable=True)  # Dietary restrictions, accessibility needs
    
    # Payment information
    payment_status = db.Column(db.Enum('pending', 'completed', 'failed', 'refunded', name='payment_status_enum'), 
                              nullable=False, default='pending')
    payment_amount = db.Column(db.Float, nullable=True)  # Amount paid (may differ from event price due to discounts)
    payment_method = db.Column(db.String(50), nullable=True)  # 'card', 'paypal', 'transfer', etc.
    payment_reference = db.Column(db.String(100), nullable=True)  # Payment gateway transaction ID
    payment_date = db.Column(db.DateTime, nullable=True)
    
    # Discount/promotion information
    discount_code = db.Column(db.String(50), nullable=True)
    discount_amount = db.Column(db.Float, default=0.0, nullable=False)
    discount_percentage = db.Column(db.Float, default=0.0, nullable=False)
    
    # Event participation
    checked_in = db.Column(db.Boolean, default=False, nullable=False)
    check_in_time = db.Column(db.DateTime, nullable=True)
    checked_out = db.Column(db.Boolean, default=False, nullable=False)
    check_out_time = db.Column(db.DateTime, nullable=True)
    attended = db.Column(db.Boolean, default=False, nullable=False)  # Did they actually attend?
    
    # Approval workflow (for events that require approval)
    approved_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    rejection_reason = db.Column(db.Text, nullable=True)
    
    # Emergency contact information
    emergency_contact_name = db.Column(db.String(100), nullable=True)
    emergency_contact_phone = db.Column(db.String(20), nullable=True)
    
    # Timestamps
    registered_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    cancelled_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    # event, user, dog relationships created via backref in respective models
    dog = db.relationship('Dog', backref='event_registrations')
    approved_by = db.relationship('User', foreign_keys=[approved_by_user_id])
    
    # Ensure one registration per user per event
    __table_args__ = (
        db.UniqueConstraint('event_id', 'user_id', name='unique_user_event_registration'),
    )
    
    def __init__(self, event_id, user_id, dog_id=None, **kwargs):
        """
        Initialize EventRegistration instance
        Required fields: event_id, user_id
        Optional fields: dog_id
        """
        self.event_id = event_id
        self.user_id = user_id
        self.dog_id = dog_id
        self.registration_code = self.generate_registration_code()
        
        # Set initial status based on event requirements
        from app.models.event import Event
        event = Event.query.get(event_id)
        if event and event.requires_approval:
            self.status = 'pending'
        else:
            self.status = 'confirmed'
        
        # Set payment amount to event price (before discounts)
        if event:
            self.payment_amount = event.price
        
        # Set optional fields
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def generate_registration_code(self):
        """Generate unique registration/ticket code"""
        import string
        import random
        
        # Generate format: DM-XXXXXX (DogMatch + 6 random characters)
        code_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        return f"DM-{code_suffix}"
    
    def calculate_final_amount(self):
        """Calculate final payment amount after discounts"""
        base_amount = self.payment_amount or 0
        
        if self.discount_percentage > 0:
            discount = base_amount * (self.discount_percentage / 100)
            return max(0, base_amount - discount)
        elif self.discount_amount > 0:
            return max(0, base_amount - self.discount_amount)
        
        return base_amount
    
    def apply_discount(self, discount_code=None, discount_percentage=0, discount_amount=0):
        """Apply discount to registration"""
        self.discount_code = discount_code
        self.discount_percentage = discount_percentage
        self.discount_amount = discount_amount
        
        # Recalculate payment amount
        self.payment_amount = self.calculate_final_amount()
        db.session.commit()
    
    def can_be_cancelled_by(self, user_id):
        """Check if registration can be cancelled by user"""
        # User can cancel their own registration
        if self.user_id == user_id:
            return True
        
        # Event organizer can cancel registrations
        if self.event.organizer_id == user_id:
            return True
        
        # Admin can cancel any registration
        from app.models.user import User
        user = User.query.get(user_id)
        if user and user.is_admin():
            return True
        
        return False
    
    def can_be_approved_by(self, user_id):
        """Check if registration can be approved by user"""
        # Only event organizer can approve
        if self.event.organizer_id == user_id:
            return True
        
        # Admin can approve any registration
        from app.models.user import User
        user = User.query.get(user_id)
        if user and user.is_admin():
            return True
        
        return False
    
    def approve_registration(self, approved_by_user_id):
        """Approve the registration"""
        if self.status != 'pending':
            raise ValueError("Only pending registrations can be approved")
        
        self.status = 'confirmed'
        self.approved_by_user_id = approved_by_user_id
        self.approved_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
        # Update event participant count
        self.event.update_participant_count()
        
        db.session.commit()
        
        # TODO: Send confirmation notification to user
    
    def reject_registration(self, rejected_by_user_id, reason=None):
        """Reject the registration"""
        if self.status != 'pending':
            raise ValueError("Only pending registrations can be rejected")
        
        self.status = 'rejected'
        self.approved_by_user_id = rejected_by_user_id  # Track who rejected
        self.rejection_reason = reason
        self.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # TODO: Send rejection notification to user
    
    def cancel_registration(self, cancelled_by_user_id, reason=None):
        """Cancel the registration"""
        if self.status in ['cancelled', 'rejected']:
            raise ValueError("Registration is already cancelled or rejected")
        
        old_status = self.status
        self.status = 'cancelled'
        self.cancelled_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
        # If was confirmed, update event participant count
        if old_status == 'confirmed':
            self.event.update_participant_count()
        
        # Handle refunds if payment was made
        if self.payment_status == 'completed':
            self.process_refund()
        
        db.session.commit()
        
        # TODO: Send cancellation notification
    
    def process_payment(self, payment_method, payment_reference=None):
        """Process payment for registration"""
        self.payment_status = 'completed'
        self.payment_method = payment_method
        self.payment_reference = payment_reference
        self.payment_date = datetime.utcnow()
        
        # If event doesn't require approval, confirm registration immediately
        if not self.event.requires_approval and self.status == 'pending':
            self.status = 'confirmed'
            self.event.update_participant_count()
        
        db.session.commit()
        
        # TODO: Send payment confirmation
    
    def process_refund(self, refund_amount=None):
        """Process refund for cancelled registration"""
        if self.payment_status != 'completed':
            raise ValueError("Cannot refund payment that wasn't completed")
        
        self.payment_status = 'refunded'
        
        # TODO: Integrate with payment gateway for actual refund
        # TODO: Send refund confirmation
        
        db.session.commit()
    
    def check_in_participant(self, checked_in_by_user_id=None):
        """Check in participant at event"""
        if self.status != 'confirmed':
            raise ValueError("Only confirmed registrations can be checked in")
        
        if self.checked_in:
            raise ValueError("Participant already checked in")
        
        self.checked_in = True
        self.check_in_time = datetime.utcnow()
        self.attended = True  # Mark as attended when checked in
        
        db.session.commit()
    
    def check_out_participant(self, checked_out_by_user_id=None):
        """Check out participant from event"""
        if not self.checked_in:
            raise ValueError("Cannot check out participant who wasn't checked in")
        
        if self.checked_out:
            raise ValueError("Participant already checked out")
        
        self.checked_out = True
        self.check_out_time = datetime.utcnow()
        
        db.session.commit()
    
    def is_eligible_for_refund(self):
        """Check if registration is eligible for refund"""
        if self.payment_status != 'completed':
            return False
        
        # Check if event hasn't started yet
        if not self.event.is_upcoming():
            return False
        
        # Check if within refund window (e.g., 24 hours before event)
        time_until_event = self.event.event_date - datetime.utcnow()
        refund_deadline = timedelta(hours=24)
        
        return time_until_event > refund_deadline
    
    def get_qr_code_data(self):
        """Generate QR code data for check-in"""
        return {
            'registration_code': self.registration_code,
            'event_id': self.event_id,
            'user_id': self.user_id,
            'dog_id': self.dog_id,
            'registered_at': self.registered_at.isoformat()
        }
    
    def to_dict(self, include_event=False, include_user=False, include_dog=False, current_user_id=None):
        """
        Convert registration to dictionary for JSON responses
        include_event: Whether to include event information
        include_user: Whether to include user information  
        include_dog: Whether to include dog information
        current_user_id: ID of user viewing the registration (affects perspective)
        """
        data = {
            'id': self.id,
            'event_id': self.event_id,
            'user_id': self.user_id,
            'dog_id': self.dog_id,
            'registration_code': self.registration_code,
            'status': self.status,
            'notes': self.notes,
            'special_requests': self.special_requests,
            'payment_status': self.payment_status,
            'payment_amount': self.payment_amount,
            'payment_method': self.payment_method,
            'payment_date': self.payment_date.isoformat() if self.payment_date else None,
            'discount_code': self.discount_code,
            'discount_amount': self.discount_amount,
            'discount_percentage': self.discount_percentage,
            'final_amount': self.calculate_final_amount(),
            'checked_in': self.checked_in,
            'check_in_time': self.check_in_time.isoformat() if self.check_in_time else None,
            'checked_out': self.checked_out,
            'check_out_time': self.check_out_time.isoformat() if self.check_out_time else None,
            'attended': self.attended,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'rejection_reason': self.rejection_reason,
            'emergency_contact_name': self.emergency_contact_name,
            'emergency_contact_phone': self.emergency_contact_phone,
            'registered_at': self.registered_at.isoformat() if self.registered_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'cancelled_at': self.cancelled_at.isoformat() if self.cancelled_at else None
        }
        
        if include_event:
            data['event'] = self.event.to_dict(include_organizer=True)
        
        if include_user:
            data['user'] = self.user.to_dict()
        
        if include_dog:
            data['dog'] = self.dog.to_dict(include_owner=False, include_photos=True)
        
        if current_user_id:
            data.update({
                'is_my_registration': self.user_id == current_user_id,
                'can_cancel': self.can_be_cancelled_by(current_user_id),
                'can_approve': self.can_be_approved_by(current_user_id),
                'is_eligible_for_refund': self.is_eligible_for_refund()
            })
        
        return data
    
    @staticmethod
    def get_user_registration_for_event(user_id, event_id):
        """Get user's registration for a specific event"""
        return EventRegistration.query.filter(
            EventRegistration.user_id == user_id,
            EventRegistration.event_id == event_id
        ).first()
    
    @staticmethod
    def get_confirmed_registrations_for_event(event_id):
        """Get all confirmed registrations for an event"""
        return EventRegistration.query.filter(
            EventRegistration.event_id == event_id,
            EventRegistration.status == 'confirmed'
        ).all()
    
    @staticmethod
    def get_pending_registrations_for_event(event_id):
        """Get all pending registrations for an event (requiring approval)"""
        return EventRegistration.query.filter(
            EventRegistration.event_id == event_id,
            EventRegistration.status == 'pending'
        ).all()
    
    def __repr__(self):
        """String representation for debugging"""
        return f'<EventRegistration {self.id}: User {self.user_id} → Event {self.event_id} ({self.status})>'


