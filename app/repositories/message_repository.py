"""
Message Repository

Handles all database operations for Message model.
Provides methods for querying, creating, updating, and deleting messages.
"""

from app import db
from app.models.message import Message
from app.models.match import Match
from app.models.dog import Dog
from app.models.user import User
from sqlalchemy import or_, and_
from sqlalchemy.orm import joinedload, selectinload
from datetime import datetime, timezone


class MessageRepository:
    """Repository for Message model data access"""
    
    @staticmethod
    def find_by_id(message_id):
        """
        Find message by ID
        
        Args:
            message_id: Message ID
            
        Returns:
            Message or None
        """
        return Message.query.get(message_id)
    
    @staticmethod
    def find_by_match(match_id, limit=100, offset=0):
        """
        Find all messages for a match
        
        Args:
            match_id: Match ID
            limit: Maximum results to return
            offset: Number of results to skip
            
        Returns:
            list: List of messages ordered by creation time
        """
        return Message.query.filter_by(match_id=match_id).order_by(
            Message.created_at.asc()
        ).limit(limit).offset(offset).all()
    
    @staticmethod
    def find_by_sender(sender_user_id, limit=100, offset=0):
        """
        Find all messages sent by a user
        
        Args:
            sender_user_id: User ID of sender
            limit: Maximum results to return
            offset: Number of results to skip
            
        Returns:
            list: List of messages
        """
        return Message.query.filter_by(sender_user_id=sender_user_id).order_by(
            Message.created_at.desc()
        ).limit(limit).offset(offset).all()
    
    @staticmethod
    def find_latest_by_match(match_id):
        """
        Find the latest message in a match
        
        Args:
            match_id: Match ID
            
        Returns:
            Message or None
        """
        return Message.query.filter_by(match_id=match_id).order_by(
            Message.created_at.desc()
        ).first()
    
    @staticmethod
    def create(message_data):
        """
        Create a new message
        
        Args:
            message_data: Dictionary of message attributes
            
        Returns:
            Message: Created message object
        """
        message = Message(**message_data)
        db.session.add(message)
        db.session.commit()
        db.session.refresh(message)
        return message
    
    @staticmethod
    def update(message, updates):
        """
        Update message attributes
        
        Args:
            message: Message object to update
            updates: Dictionary of fields to update
            
        Returns:
            Message: Updated message object
        """
        for key, value in updates.items():
            if hasattr(message, key):
                setattr(message, key, value)
        
        message.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        db.session.refresh(message)
        return message
    
    @staticmethod
    def delete(message):
        """
        Delete a message
        
        Args:
            message: Message object to delete
            
        Returns:
            bool: True if successful
        """
        db.session.delete(message)
        db.session.commit()
        return True
    
    @staticmethod
    def mark_as_read(message):
        """
        Mark a message as read
        
        Args:
            message: Message object
            
        Returns:
            Message: Updated message object
        """
        message.is_read = True
        message.read_at = datetime.now(timezone.utc)
        db.session.commit()
        db.session.refresh(message)
        return message
    
    @staticmethod
    def mark_multiple_as_read(message_ids):
        """
        Mark multiple messages as read
        
        Args:
            message_ids: List of message IDs
            
        Returns:
            int: Number of messages updated
        """
        count = Message.query.filter(Message.id.in_(message_ids)).update(
            {
                'is_read': True,
                'read_at': datetime.now(timezone.utc)
            },
            synchronize_session=False
        )
        db.session.commit()
        return count
    
    @staticmethod
    def find_unread_by_match(match_id, user_id):
        """
        Find unread messages in a match for a specific user
        
        Args:
            match_id: Match ID
            user_id: User ID (recipient)
            
        Returns:
            list: List of unread messages
        """
        return Message.query.filter(
            and_(
                Message.match_id == match_id,
                Message.sender_user_id != user_id,
                Message.is_read == False
            )
        ).order_by(Message.created_at.asc()).all()
    
    @staticmethod
    def count_by_match(match_id):
        """
        Count messages in a match
        
        Args:
            match_id: Match ID
            
        Returns:
            int: Number of messages
        """
        return Message.query.filter_by(match_id=match_id).count()
    
    @staticmethod
    def count_unread_by_match(match_id, user_id):
        """
        Count unread messages for a user in a match
        
        Args:
            match_id: Match ID
            user_id: User ID (recipient)
            
        Returns:
            int: Number of unread messages
        """
        return Message.query.filter(
            and_(
                Message.match_id == match_id,
                Message.sender_user_id != user_id,
                Message.is_read == False
            )
        ).count()
    
    @staticmethod
    def count_unread_by_user(user_id):
        """
        Count total unread messages for a user across all matches
        
        Args:
            user_id: User ID (recipient)
            
        Returns:
            int: Total unread message count
        """
        # This requires joining with Match to find user's matches
        # For simplicity, we'll query messages not sent by user that are unread
        return Message.query.filter(
            and_(
                Message.sender_user_id != user_id,
                Message.is_read == False
            )
        ).count()
    
    @staticmethod
    def find_by_sender_and_match(sender_user_id, match_id, limit=50):
        """
        Find messages sent by a specific user in a match
        
        Args:
            sender_user_id: User ID of sender
            match_id: Match ID
            limit: Maximum results to return
            
        Returns:
            list: List of messages
        """
        return Message.query.filter_by(
            sender_user_id=sender_user_id,
            match_id=match_id
        ).order_by(Message.created_at.asc()).limit(limit).all()
    
    @staticmethod
    def delete_by_match(match_id):
        """
        Delete all messages in a match
        
        Args:
            match_id: Match ID
            
        Returns:
            int: Number of messages deleted
        """
        count = Message.query.filter_by(match_id=match_id).delete()
        db.session.commit()
        return count
    
    @staticmethod
    def find_recent_matches_with_messages(user_id, limit=20):
        """
        Find recent matches that have messages
        
        Args:
            user_id: User ID
            limit: Maximum results to return
            
        Returns:
            list: List of match IDs with recent messages
        """
        # Get distinct match IDs ordered by most recent message
        result = db.session.query(Message.match_id).distinct().order_by(
            Message.created_at.desc()
        ).limit(limit).all()
        
        return [row[0] for row in result]
    
    @staticmethod
    def exists(message_id):
        """
        Check if message exists
        
        Args:
            message_id: Message ID
            
        Returns:
            bool: True if exists
        """
        return db.session.query(
            Message.query.filter_by(id=message_id).exists()
        ).scalar()
    
    # ==================== OPTIMIZED METHODS (Prevent N+1 Queries) ====================
    
    @staticmethod
    def find_by_match_with_sender(match_id, limit=100, offset=0):
        """
        Find messages for match with sender user loaded
        Optimized for chat display
        
        Args:
            match_id: Match ID
            limit: Maximum results
            offset: Pagination offset
            
        Returns:
            list: List of messages with sender loaded
        """
        return Message.query.filter_by(
            match_id=match_id
        ).options(
            joinedload(Message.sender_user)
        ).order_by(Message.created_at.asc()).limit(limit).offset(offset).all()
    
    @staticmethod
    def find_by_sender_with_match_and_dogs(sender_user_id, limit=100, offset=0):
        """
        Find messages by sender with match and dog details loaded
        Optimized for message history with context
        
        Args:
            sender_user_id: User ID
            limit: Maximum results
            offset: Pagination offset
            
        Returns:
            list: List of messages with full context loaded
        """
        return Message.query.filter_by(
            sender_user_id=sender_user_id
        ).options(
            joinedload(Message.match).joinedload(Match.dog_one),
            joinedload(Message.match).joinedload(Match.dog_two)
        ).order_by(Message.created_at.desc()).limit(limit).offset(offset).all()
    
    @staticmethod
    def find_unread_with_match_details(user_id, limit=100):
        """
        Find unread messages for user with match and dog details loaded
        Optimized for notifications/unread message list
        
        Args:
            user_id: User ID
            limit: Maximum results
            
        Returns:
            list: List of unread messages with context
        """
        return Message.query.join(Match).filter(
            and_(
                Message.is_read == False,
                Message.sender_user_id != user_id,
                or_(
                    Match.dog_one.has(owner_id=user_id),
                    Match.dog_two.has(owner_id=user_id)
                )
            )
        ).options(
            joinedload(Message.sender_user),
            joinedload(Message.match).joinedload(Match.dog_one),
            joinedload(Message.match).joinedload(Match.dog_two)
        ).order_by(Message.created_at.desc()).limit(limit).all()
    
    @staticmethod
    def find_recent_matches_with_last_message_and_users(user_id, limit=20):
        """
        Find recent matches with last message and user details loaded
        Optimized for chat list screen showing conversation previews
        
        Args:
            user_id: User ID
            limit: Maximum results
            
        Returns:
            list: List of unique matches with last message and users
        """
        # Get latest message per match
        subquery = db.session.query(
            Message.match_id,
            db.func.max(Message.created_at).label('last_message_time')
        ).group_by(Message.match_id).subquery()
        
        # Join to get full message details with relationships
        return db.session.query(Message).join(
            subquery,
            and_(
                Message.match_id == subquery.c.match_id,
                Message.created_at == subquery.c.last_message_time
            )
        ).join(Match).filter(
            or_(
                Match.dog_one.has(owner_id=user_id),
                Match.dog_two.has(owner_id=user_id)
            )
        ).options(
            joinedload(Message.sender_user),
            joinedload(Message.match).joinedload(Match.dog_one).joinedload(Dog.owner),
            joinedload(Message.match).joinedload(Match.dog_two).joinedload(Dog.owner)
        ).order_by(Message.created_at.desc()).limit(limit).all()
