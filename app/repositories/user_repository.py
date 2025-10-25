"""
User Repository

Handles all database operations for User and BlacklistedToken models.
Provides methods for querying, creating, updating, and deleting users.
"""

from app import db
from app.models.user import User, BlacklistedToken
from sqlalchemy import or_
from datetime import datetime, timezone


class UserRepository:
    """Repository for User model data access"""
    
    @staticmethod
    def find_by_id(user_id):
        """
        Find user by ID
        
        Args:
            user_id: User ID
            
        Returns:
            User or None
        """
        return User.query.get(user_id)
    
    @staticmethod
    def find_by_email(email):
        """
        Find user by email (case-insensitive)
        
        Args:
            email: User email
            
        Returns:
            User or None
        """
        return User.query.filter_by(email=email.lower()).first()
    
    @staticmethod
    def find_by_username(username):
        """
        Find user by username
        
        Args:
            username: Username
            
        Returns:
            User or None
        """
        return User.query.filter_by(username=username).first()
    
    @staticmethod
    def find_by_email_or_username(identifier):
        """
        Find user by email or username
        
        Args:
            identifier: Email or username
            
        Returns:
            User or None
        """
        return User.query.filter(
            or_(
                User.email == identifier.lower(),
                User.username == identifier
            )
        ).first()
    
    @staticmethod
    def create(user_data):
        """
        Create a new user
        
        Args:
            user_data: Dictionary of user attributes
            
        Returns:
            User: Created user object
        """
        user = User(**user_data)
        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)  # Refresh to get computed fields
        return user
    
    @staticmethod
    def update(user, updates):
        """
        Update user attributes
        
        Args:
            user: User object to update
            updates: Dictionary of fields to update
            
        Returns:
            User: Updated user object
        """
        for key, value in updates.items():
            if hasattr(user, key):
                setattr(user, key, value)
        
        user.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        db.session.refresh(user)
        return user
    
    @staticmethod
    def delete(user):
        """
        Delete a user
        
        Args:
            user: User object to delete
            
        Returns:
            bool: True if successful
        """
        db.session.delete(user)
        db.session.commit()
        return True
    
    @staticmethod
    def search(query, limit=20, offset=0):
        """
        Search users by username, first name, or last name
        
        Args:
            query: Search string
            limit: Maximum results to return
            offset: Number of results to skip
            
        Returns:
            list: List of matching users
        """
        pattern = f"%{query}%"
        return User.query.filter(
            or_(
                User.username.ilike(pattern),
                User.first_name.ilike(pattern),
                User.last_name.ilike(pattern)
            )
        ).limit(limit).offset(offset).all()
    
    @staticmethod
    def find_all(limit=100, offset=0):
        """
        Get all users with pagination
        
        Args:
            limit: Maximum results to return
            offset: Number of results to skip
            
        Returns:
            list: List of users
        """
        return User.query.limit(limit).offset(offset).all()
    
    @staticmethod
    def count():
        """
        Count total users
        
        Returns:
            int: Total user count
        """
        return User.query.count()
    
    @staticmethod
    def find_verified_users(limit=100):
        """
        Find all verified users
        
        Args:
            limit: Maximum results to return
            
        Returns:
            list: List of verified users
        """
        return User.query.filter_by(is_verified=True).limit(limit).all()
    
    @staticmethod
    def find_by_location(city=None, state=None, country=None, limit=50):
        """
        Find users by location
        
        Args:
            city: City name
            state: State name
            country: Country name
            limit: Maximum results to return
            
        Returns:
            list: List of users in location
        """
        query = User.query
        
        if city:
            query = query.filter(User.city.ilike(f"%{city}%"))
        if state:
            query = query.filter(User.state.ilike(f"%{state}%"))
        if country:
            query = query.filter(User.country.ilike(f"%{country}%"))
        
        return query.limit(limit).all()
    
    @staticmethod
    def exists_by_email(email):
        """
        Check if user exists with given email
        
        Args:
            email: Email to check
            
        Returns:
            bool: True if exists
        """
        return db.session.query(
            User.query.filter_by(email=email.lower()).exists()
        ).scalar()
    
    @staticmethod
    def exists_by_username(username):
        """
        Check if user exists with given username
        
        Args:
            username: Username to check
            
        Returns:
            bool: True if exists
        """
        return db.session.query(
            User.query.filter_by(username=username).exists()
        ).scalar()


class BlacklistedTokenRepository:
    """Repository for BlacklistedToken model data access"""
    
    @staticmethod
    def create(jti, user_id, expires_at):
        """
        Add token to blacklist
        
        Args:
            jti: JWT token ID
            user_id: User ID
            expires_at: Token expiration datetime
            
        Returns:
            BlacklistedToken: Created blacklist entry
        """
        token = BlacklistedToken(
            jti=jti,
            user_id=user_id,
            expires_at=expires_at
        )
        db.session.add(token)
        db.session.commit()
        return token
    
    @staticmethod
    def find_by_jti(jti):
        """
        Find blacklisted token by JTI
        
        Args:
            jti: JWT token ID
            
        Returns:
            BlacklistedToken or None
        """
        return BlacklistedToken.query.filter_by(jti=jti).first()
    
    @staticmethod
    def is_blacklisted(jti):
        """
        Check if token is blacklisted
        
        Args:
            jti: JWT token ID
            
        Returns:
            bool: True if blacklisted
        """
        return db.session.query(
            BlacklistedToken.query.filter_by(jti=jti).exists()
        ).scalar()
    
    @staticmethod
    def delete_expired():
        """
        Delete expired blacklisted tokens
        
        Returns:
            int: Number of tokens deleted
        """
        count = BlacklistedToken.query.filter(
            BlacklistedToken.expires_at < datetime.now(timezone.utc)
        ).delete()
        db.session.commit()
        return count
    
    @staticmethod
    def delete_by_user(user_id):
        """
        Delete all blacklisted tokens for a user
        
        Args:
            user_id: User ID
            
        Returns:
            int: Number of tokens deleted
        """
        count = BlacklistedToken.query.filter_by(user_id=user_id).delete()
        db.session.commit()
        return count
