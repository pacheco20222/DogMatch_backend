# app/models/message.py
from datetime import datetime
from app import db

class Message(db.Model):
    """
    Message model for DogMatch application
    Handles chat messages between matched users
    """
    
    # Table configuration
    __tablename__ = 'messages'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Foreign key to Match (which dogs are chatting)
    match_id = db.Column(db.Integer, db.ForeignKey('matches.id'), nullable=False)
    
    # Foreign key to User (who sent the message)
    sender_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Message content
    content = db.Column(db.Text, nullable=False)
    message_type = db.Column(db.Enum('text', 'image', 'location', 'system', name='message_type_enum'), 
                           nullable=False, default='text')
    
    # Message metadata
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    is_edited = db.Column(db.Boolean, default=False, nullable=False)
    edited_at = db.Column(db.DateTime, nullable=True)
    
    # For image messages
    image_url = db.Column(db.String(500), nullable=True)
    image_filename = db.Column(db.String(255), nullable=True)
    
    # For location messages  
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    location_name = db.Column(db.String(200), nullable=True)  # "Central Park, NYC"
    
    # For system messages (match notifications, etc.)
    system_data = db.Column(db.Text, nullable=True)  # JSON data for system messages
    
    # Timestamps
    sent_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    delivered_at = db.Column(db.DateTime, nullable=True)
    read_at = db.Column(db.DateTime, nullable=True)
    
    # Soft delete (for message recall/deletion)
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)
    deleted_at = db.Column(db.DateTime, nullable=True)
    deleted_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Relationships
    # match relationship created via backref in Match model
    # sender relationship created via backref below
    sender = db.relationship('User', foreign_keys=[sender_user_id], backref='sent_messages')
    deleted_by = db.relationship('User', foreign_keys=[deleted_by_user_id])
    
    def __init__(self, match_id, sender_user_id, content, message_type='text', **kwargs):
        """
        Initialize Message instance
        Required fields: match_id, sender_user_id, content
        """
        self.match_id = match_id
        self.sender_user_id = sender_user_id
        self.content = content.strip() if content else ''
        self.message_type = message_type
        
        # Set optional fields
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def mark_as_read(self, read_by_user_id=None):
        """Mark message as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = datetime.utcnow()
            db.session.commit()
            
            # Update match message stats
            self.match.update_message_stats()
    
    def mark_as_delivered(self):
        """Mark message as delivered"""
        if not self.delivered_at:
            self.delivered_at = datetime.utcnow()
            db.session.commit()
    
    def edit_content(self, new_content):
        """Edit message content"""
        if self.message_type != 'text':
            raise ValueError("Only text messages can be edited")
        
        self.content = new_content.strip()
        self.is_edited = True
        self.edited_at = datetime.utcnow()
        db.session.commit()
    
    def soft_delete(self, deleted_by_user_id):
        """Soft delete message (mark as deleted without removing from DB)"""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
        self.deleted_by_user_id = deleted_by_user_id
        db.session.commit()
        
        # Update match message stats
        self.match.update_message_stats()
    
    def can_be_edited_by(self, user_id):
        """Check if user can edit this message"""
        # Only sender can edit, and only within time limit (e.g., 15 minutes)
        if self.sender_user_id != user_id:
            return False
        
        if self.message_type != 'text':
            return False
        
        # Allow editing within 15 minutes
        time_limit = datetime.utcnow() - self.sent_at
        return time_limit.total_seconds() < 900  # 15 minutes
    
    def can_be_deleted_by(self, user_id):
        """Check if user can delete this message"""
        # Sender can always delete their own messages
        if self.sender_user_id == user_id:
            return True
        
        # Match participants can delete messages in their conversation
        match_user_ids = [self.match.dog_one.owner_id, self.match.dog_two.owner_id]
        return user_id in match_user_ids
    
    def get_recipient_user_id(self):
        """Get the user ID of the message recipient"""
        match_user_ids = [self.match.dog_one.owner_id, self.match.dog_two.owner_id]
        # Return the user ID that's not the sender
        return next((uid for uid in match_user_ids if uid != self.sender_user_id), None)
    
    def is_system_message(self):
        """Check if this is a system-generated message"""
        return self.message_type == 'system'
    
    def is_media_message(self):
        """Check if this message contains media (image/location)"""
        return self.message_type in ['image', 'location']
    
    def get_display_content(self):
        """Get content for display (handles different message types)"""
        if self.is_deleted:
            return "This message was deleted"
        
        if self.message_type == 'text':
            return self.content
        elif self.message_type == 'image':
            return f"📷 Image: {self.image_filename or 'Photo'}"
        elif self.message_type == 'location':
            return f"📍 Location: {self.location_name or 'Shared location'}"
        elif self.message_type == 'system':
            return self._format_system_message()
        
        return self.content
    
    def _format_system_message(self):
        """Format system message content"""
        if not self.system_data:
            return self.content
        
        import json
        try:
            data = json.loads(self.system_data)
            msg_type = data.get('type', 'unknown')
            
            if msg_type == 'match_created':
                return "🎉 You have a new match!"
            elif msg_type == 'first_message':
                return "💬 Say hello to start the conversation!"
            elif msg_type == 'adoption_interest':
                return f"❤️ {data.get('user_name')} is interested in adoption!"
            
        except (json.JSONDecodeError, KeyError):
            pass
        
        return self.content
    
    def to_dict(self, include_match_info=False, current_user_id=None):
        """
        Convert message to dictionary for JSON responses
        include_match_info: Whether to include basic match information
        current_user_id: ID of user viewing the message (affects perspective)
        """
        data = {
            'id': self.id,
            'match_id': self.match_id,
            'sender_user_id': self.sender_user_id,
            'content': self.get_display_content(),
            'raw_content': self.content if not self.is_deleted else None,
            'message_type': self.message_type,
            'is_read': self.is_read,
            'is_edited': self.is_edited,
            'is_deleted': self.is_deleted,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'delivered_at': self.delivered_at.isoformat() if self.delivered_at else None,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'edited_at': self.edited_at.isoformat() if self.edited_at else None
        }
        
        # Sender information
        data['sender'] = {
            'user_id': self.sender_user_id,
            'username': self.sender.username,
            'full_name': self.sender.get_full_name()
        }
        
        # Add perspective info if current_user_id provided
        if current_user_id:
            data['is_sent_by_me'] = self.sender_user_id == current_user_id
            data['can_edit'] = self.can_be_edited_by(current_user_id)
            data['can_delete'] = self.can_be_deleted_by(current_user_id)
        
        # Media content
        if self.message_type == 'image':
            data.update({
                'image_url': self.image_url,
                'image_filename': self.image_filename
            })
        elif self.message_type == 'location':
            data.update({
                'latitude': self.latitude,
                'longitude': self.longitude,
                'location_name': self.location_name
            })
        elif self.message_type == 'system':
            data['system_data'] = self.system_data
        
        # Match information (optional)
        if include_match_info:
            data['match'] = {
                'id': self.match.id,
                'status': self.match.status,
                'participants': [
                    {
                        'user_id': self.match.dog_one.owner_id,
                        'username': self.match.dog_one.owner.username,
                        'dog_name': self.match.dog_one.name
                    },
                    {
                        'user_id': self.match.dog_two.owner_id,
                        'username': self.match.dog_two.owner.username,
                        'dog_name': self.match.dog_two.name
                    }
                ]
            }
        
        return data
    
    @staticmethod
    def create_system_message(match_id, message_type, content, system_data=None):
        """Create a system message for match events"""
        import json
        
        # Use a system user ID (you might want to create a system user)
        system_user_id = 1  # Assuming user ID 1 is system/admin
        
        message = Message(
            match_id=match_id,
            sender_user_id=system_user_id,
            content=content,
            message_type='system',
            system_data=json.dumps(system_data) if system_data else None
        )
        
        db.session.add(message)
        db.session.commit()
        return message
    
    def __repr__(self):
        """String representation for debugging"""
        return f'<Message {self.id}: {self.message_type} in Match {self.match_id}>'
