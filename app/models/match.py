# match.py
from datetime import datetime
from app import db

class Match(db.Model):
    """
    Match model for DogMatch application
    Handles swipe results and mutual matches between dogs
    """
    
    # Table configuration
    __tablename__ = 'matches'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Foreign keys to Dog model (many-to-many through matches)
    dog_one_id = db.Column(db.Integer, db.ForeignKey('dogs.id'), nullable=False)  
    dog_two_id = db.Column(db.Integer, db.ForeignKey('dogs.id'), nullable=False)  
    
    # Match status and type
    status = db.Column(db.Enum('pending', 'matched', 'declined', 'expired', name='match_status_enum'), 
                      nullable=False, default='pending')
    
    # Who initiated the match (which dog swiped first)
    initiated_by_dog_id = db.Column(db.Integer, db.ForeignKey('dogs.id'), nullable=False)
    
    # Swipe actions from each dog
    dog_one_action = db.Column(db.Enum('like', 'pass', 'super_like', 'pending', name='swipe_action_enum'), 
                              nullable=False, default='pending')
    dog_two_action = db.Column(db.Enum('like', 'pass', 'super_like', 'pending', name='swipe_action_enum'), 
                              nullable=False, default='pending')
    
    # Match metadata
    match_type = db.Column(db.Enum('playdate', 'adoption', 'general', name='match_type_enum'), 
                          nullable=False, default='general')
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    matched_at = db.Column(db.DateTime, nullable=True)  # When both dogs liked each other
    expires_at = db.Column(db.DateTime, nullable=True)  # When pending match expires
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Activity tracking
    last_message_at = db.Column(db.DateTime, nullable=True)
    message_count = db.Column(db.Integer, default=0, nullable=False)
    
    # Match settings
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_archived = db.Column(db.Boolean, default=False, nullable=False)
    archived_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Relationships are created via backref in Dog model:
    # dog_one, dog_two relationships created in dog.py
    # messages relationship will be created when we build Message model
    messages = db.relationship('Message', backref='match', lazy='dynamic', cascade='all, delete-orphan')
    
    # Constraints to prevent duplicate matches and self-matches
    __table_args__ = (
        db.UniqueConstraint('dog_one_id', 'dog_two_id', name='unique_match_pair'),
        db.CheckConstraint('dog_one_id != dog_two_id', name='no_self_match'),
        db.CheckConstraint('dog_one_id < dog_two_id', name='ordered_match_pair'),  # Ensure consistent ordering
    )
    
    def __init__(self, dog_one_id, dog_two_id, initiated_by_dog_id, action='like', **kwargs):
        """
        Initialize Match instance
        Automatically orders dog IDs to prevent duplicates
        """
        # Ensure consistent ordering (smaller ID first)
        if dog_one_id > dog_two_id:
            dog_one_id, dog_two_id = dog_two_id, dog_one_id
        
        self.dog_one_id = dog_one_id
        self.dog_two_id = dog_two_id
        self.initiated_by_dog_id = initiated_by_dog_id
        
        # Set the action for the initiating dog
        if initiated_by_dog_id == dog_one_id:
            self.dog_one_action = action
            self.dog_two_action = 'pending'
        else:
            self.dog_two_action = action
            self.dog_one_action = 'pending'
        
        # Set optional fields
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def update_action(self, dog_id, action):
        """
        Update swipe action for a specific dog
        Automatically updates match status if both dogs have acted
        """
        if dog_id == self.dog_one_id:
            self.dog_one_action = action
        elif dog_id == self.dog_two_id:
            self.dog_two_action = action
        else:
            raise ValueError("Dog ID does not belong to this match")
        
        # Update match status based on actions
        self._update_match_status()
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def _update_match_status(self):
        """Internal method to update match status based on dog actions"""
        if self.dog_one_action == 'pending' or self.dog_two_action == 'pending':
            self.status = 'pending'
        elif self.dog_one_action == 'like' and self.dog_two_action == 'like':
            self.status = 'matched'
            if not self.matched_at:
                self.matched_at = datetime.utcnow()
        elif self.dog_one_action == 'super_like' or self.dog_two_action == 'super_like':
            # Super like creates immediate match (even if other hasn't responded)
            if self.dog_one_action in ['like', 'super_like'] and self.dog_two_action in ['like', 'super_like']:
                self.status = 'matched'
                if not self.matched_at:
                    self.matched_at = datetime.utcnow()
        elif self.dog_one_action == 'pass' or self.dog_two_action == 'pass':
            self.status = 'declined'
    
    def is_mutual_match(self):
        """Check if both dogs have liked each other"""
        return (self.dog_one_action == 'like' and self.dog_two_action == 'like') or \
               (self.dog_one_action == 'super_like' or self.dog_two_action == 'super_like')
    
    def get_other_dog(self, current_dog_id):
        """Get the other dog in the match (not the current user's dog)"""
        if current_dog_id == self.dog_one_id:
            return self.dog_two
        elif current_dog_id == self.dog_two_id:
            return self.dog_one
        else:
            raise ValueError("Dog ID does not belong to this match")
    
    def get_dog_action(self, dog_id):
        """Get the swipe action for a specific dog"""
        if dog_id == self.dog_one_id:
            return self.dog_one_action
        elif dog_id == self.dog_two_id:
            return self.dog_two_action
        else:
            raise ValueError("Dog ID does not belong to this match")
    
    def can_send_messages(self):
        """Check if users can send messages (mutual match required)"""
        return self.status == 'matched' and self.is_active and not self.is_archived
    
    def archive_match(self, user_id):
        """Archive the match (hide from user's match list)"""
        self.is_archived = True
        self.archived_by_user_id = user_id
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def unarchive_match(self):
        """Restore archived match"""
        self.is_archived = False
        self.archived_by_user_id = None
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def update_message_stats(self):
        """Update message count and last message timestamp"""
        from app.models.message import Message  # Avoid circular import
        message_count = self.messages.count()
        last_message = self.messages.order_by(Message.sent_at.desc()).first()
        
        self.message_count = message_count
        self.last_message_at = last_message.sent_at if last_message else None
        db.session.commit()
    
    def is_expired(self):
        """Check if pending match has expired"""
        if self.status != 'pending' or not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    def expire_match(self):
        """Mark match as expired"""
        if self.status == 'pending':
            self.status = 'expired'
            self.updated_at = datetime.utcnow()
            db.session.commit()
    
    def get_match_duration(self):
        """Get how long the match has existed (if matched)"""
        if not self.matched_at:
            return None
        return datetime.utcnow() - self.matched_at
    
    def to_dict(self, current_user_id=None, include_dogs=True, include_messages=False):
        """
        Convert match to dictionary for JSON responses
        current_user_id: ID of user viewing the match (affects perspective)
        include_dogs: Whether to include dog information
        include_messages: Whether to include recent messages
        """
        data = {
            'id': self.id,
            'status': self.status,
            'match_type': self.match_type,
            'is_active': self.is_active,
            'is_archived': self.is_archived,
            'message_count': self.message_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'matched_at': self.matched_at.isoformat() if self.matched_at else None,
            'last_message_at': self.last_message_at.isoformat() if self.last_message_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_dogs:
            data.update({
                'dog_one': self.dog_one.to_dict(include_owner=True, include_photos=True),
                'dog_two': self.dog_two.to_dict(include_owner=True, include_photos=True),
                'dog_one_action': self.dog_one_action,
                'dog_two_action': self.dog_two_action
            })
            
            # If current_user_id provided, add perspective info
            if current_user_id:
                if self.dog_one.owner_id == current_user_id:
                    data['my_dog'] = data['dog_one']
                    data['other_dog'] = data['dog_two']
                    data['my_action'] = self.dog_one_action
                    data['other_action'] = self.dog_two_action
                elif self.dog_two.owner_id == current_user_id:
                    data['my_dog'] = data['dog_two']
                    data['other_dog'] = data['dog_one']
                    data['my_action'] = self.dog_two_action
                    data['other_action'] = self.dog_one_action
        
        if include_messages and self.can_send_messages():
            # Include last few messages
            from app.models.message import Message  # Avoid circular import
            recent_messages = self.messages.order_by(Message.sent_at.desc()).limit(5).all()
            data['recent_messages'] = [msg.to_dict() for msg in reversed(recent_messages)]
        
        return data
    
    @staticmethod
    def find_existing_match(dog_one_id, dog_two_id):
        """Find existing match between two dogs (regardless of order)"""
        # Ensure consistent ordering
        if dog_one_id > dog_two_id:
            dog_one_id, dog_two_id = dog_two_id, dog_one_id
        
        return Match.query.filter(
            Match.dog_one_id == dog_one_id,
            Match.dog_two_id == dog_two_id
        ).first()
    
    @staticmethod
    def create_or_update_match(dog_one_id, dog_two_id, initiated_by_dog_id, action='like'):
        """Create new match or update existing one"""
        existing_match = Match.find_existing_match(dog_one_id, dog_two_id)
        
        if existing_match:
            existing_match.update_action(initiated_by_dog_id, action)
            return existing_match
        else:
            new_match = Match(dog_one_id, dog_two_id, initiated_by_dog_id, action)
            db.session.add(new_match)
            db.session.commit()
            return new_match
    
    def __repr__(self):
        """String representation for debugging"""
        return f'<Match {self.id}: Dog {self.dog_one_id} & Dog {self.dog_two_id} ({self.status})>'