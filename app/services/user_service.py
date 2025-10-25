"""
User Service Layer

Handles all business logic related to user operations including:
- User creation and registration
- Profile updates
- 2FA management
- Account verification
- User queries and searches
"""

from app import db
from app.models.user import User, BlacklistedToken
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone, timedelta
import pyotp
import secrets
import logging

logger = logging.getLogger(__name__)


class UserService:
    """Service class for user-related business logic"""
    
    @staticmethod
    def create_user(email, password, username, first_name=None, last_name=None, **kwargs):
        """
        Create a new user account
        
        Args:
            email: User email address (will be lowercased)
            password: Plain text password (will be hashed)
            username: Unique username
            first_name: Optional first name
            last_name: Optional last name
            **kwargs: Additional user fields
            
        Returns:
            User: Created user object
            
        Raises:
            ValueError: If email or username already exists
        """
        # Check if email already exists
        if User.query.filter_by(email=email.lower()).first():
            raise ValueError("Email already registered")
        
        # Check if username already exists
        if User.query.filter_by(username=username).first():
            raise ValueError("Username already taken")
        
        # Hash password
        password_hash = generate_password_hash(password)
        
        # Create user
        user = User(
            email=email.lower(),
            password_hash=password_hash,
            username=username,
            first_name=first_name,
            last_name=last_name,
            **kwargs
        )
        
        db.session.add(user)
        db.session.commit()
        
        logger.info(f"User created: {user.id} - {user.email}")
        return user
    
    @staticmethod
    def authenticate(email, password):
        """
        Authenticate user with email and password
        
        Args:
            email: User email address
            password: Plain text password
            
        Returns:
            User: Authenticated user object or None
            
        Raises:
            ValueError: If account is locked or verification required
        """
        user = User.query.filter_by(email=email.lower()).first()
        
        if not user:
            return None
        
        # Check if account is locked
        if user.is_locked:
            raise ValueError("Account is locked due to too many failed login attempts")
        
        # Check if email verification required
        if not user.is_verified and user.requires_verification:
            raise ValueError("Email verification required")
        
        # Verify password
        if not check_password_hash(user.password_hash, password):
            # Increment failed login attempts
            user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
            
            # Lock account after 5 failed attempts
            if user.failed_login_attempts >= 5:
                user.is_locked = True
                user.locked_until = datetime.now(timezone.utc) + timedelta(hours=1)
                logger.warning(f"Account locked due to failed attempts: {user.email}")
            
            db.session.commit()
            return None
        
        # Reset failed login attempts on successful login
        if user.failed_login_attempts > 0:
            user.failed_login_attempts = 0
            db.session.commit()
        
        logger.info(f"User authenticated: {user.id} - {user.email}")
        return user
    
    @staticmethod
    def update_profile(user_id, updates):
        """
        Update user profile information
        
        Args:
            user_id: User ID
            updates: Dictionary of fields to update
            
        Returns:
            User: Updated user object
            
        Raises:
            ValueError: If user not found or validation fails
        """
        user = User.query.get(user_id)
        if not user:
            raise ValueError("User not found")
        
        # Fields that can be updated
        allowed_fields = [
            'first_name', 'last_name', 'username', 'bio', 'description',
            'city', 'state', 'country', 'postal_code', 'phone_number',
            'profile_photo', 'date_of_birth', 'gender', 'preferences'
        ]
        
        # Update allowed fields
        for key, value in updates.items():
            if key in allowed_fields and hasattr(user, key):
                # Check username uniqueness if changing
                if key == 'username' and value != user.username:
                    if User.query.filter_by(username=value).first():
                        raise ValueError("Username already taken")
                
                setattr(user, key, value)
        
        user.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        
        logger.info(f"User profile updated: {user.id}")
        return user
    
    @staticmethod
    def change_password(user_id, old_password, new_password):
        """
        Change user password
        
        Args:
            user_id: User ID
            old_password: Current password
            new_password: New password
            
        Returns:
            bool: True if successful
            
        Raises:
            ValueError: If user not found or old password incorrect
        """
        user = User.query.get(user_id)
        if not user:
            raise ValueError("User not found")
        
        # Verify old password
        if not check_password_hash(user.password_hash, old_password):
            raise ValueError("Current password is incorrect")
        
        # Update password
        user.password_hash = generate_password_hash(new_password)
        user.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        
        logger.info(f"Password changed for user: {user.id}")
        return True
    
    @staticmethod
    def setup_2fa(user_id):
        """
        Set up 2FA for user account
        
        Args:
            user_id: User ID
            
        Returns:
            dict: Contains secret and QR code provisioning URI
            
        Raises:
            ValueError: If user not found or 2FA already enabled
        """
        user = User.query.get(user_id)
        if not user:
            raise ValueError("User not found")
        
        if user.two_factor_enabled:
            raise ValueError("2FA is already enabled")
        
        # Generate TOTP secret
        secret = pyotp.random_base32()
        user.two_factor_secret = secret
        
        # Generate backup codes
        backup_codes = [secrets.token_hex(4) for _ in range(10)]
        user.backup_codes = backup_codes
        
        db.session.commit()
        
        # Generate provisioning URI for QR code
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=user.email,
            issuer_name="DogMatch"
        )
        
        logger.info(f"2FA setup initiated for user: {user.id}")
        
        return {
            'secret': secret,
            'provisioning_uri': provisioning_uri,
            'backup_codes': backup_codes
        }
    
    @staticmethod
    def enable_2fa(user_id, totp_code):
        """
        Enable 2FA after verifying TOTP code
        
        Args:
            user_id: User ID
            totp_code: 6-digit TOTP code
            
        Returns:
            bool: True if successful
            
        Raises:
            ValueError: If user not found or code invalid
        """
        user = User.query.get(user_id)
        if not user:
            raise ValueError("User not found")
        
        if not user.two_factor_secret:
            raise ValueError("2FA setup not initiated")
        
        # Verify TOTP code
        totp = pyotp.TOTP(user.two_factor_secret)
        if not totp.verify(totp_code):
            raise ValueError("Invalid verification code")
        
        # Enable 2FA
        user.two_factor_enabled = True
        db.session.commit()
        
        logger.info(f"2FA enabled for user: {user.id}")
        return True
    
    @staticmethod
    def disable_2fa(user_id, password):
        """
        Disable 2FA for user account
        
        Args:
            user_id: User ID
            password: User password for verification
            
        Returns:
            bool: True if successful
            
        Raises:
            ValueError: If user not found or password incorrect
        """
        user = User.query.get(user_id)
        if not user:
            raise ValueError("User not found")
        
        # Verify password
        if not check_password_hash(user.password_hash, password):
            raise ValueError("Invalid password")
        
        # Disable 2FA
        user.two_factor_enabled = False
        user.two_factor_secret = None
        user.backup_codes = []
        db.session.commit()
        
        logger.info(f"2FA disabled for user: {user.id}")
        return True
    
    @staticmethod
    def verify_email(user_id):
        """
        Mark user email as verified
        
        Args:
            user_id: User ID
            
        Returns:
            bool: True if successful
        """
        user = User.query.get(user_id)
        if not user:
            raise ValueError("User not found")
        
        user.is_verified = True
        user.verification_date = datetime.now(timezone.utc)
        db.session.commit()
        
        logger.info(f"Email verified for user: {user.id}")
        return True
    
    @staticmethod
    def get_user_by_id(user_id):
        """Get user by ID"""
        return User.query.get(user_id)
    
    @staticmethod
    def get_user_by_email(email):
        """Get user by email"""
        return User.query.filter_by(email=email.lower()).first()
    
    @staticmethod
    def get_user_by_username(username):
        """Get user by username"""
        return User.query.filter_by(username=username).first()
    
    @staticmethod
    def search_users(query, limit=20):
        """
        Search users by username, first name, or last name
        
        Args:
            query: Search query string
            limit: Maximum results to return
            
        Returns:
            list: List of matching users
        """
        search_pattern = f"%{query}%"
        users = User.query.filter(
            db.or_(
                User.username.ilike(search_pattern),
                User.first_name.ilike(search_pattern),
                User.last_name.ilike(search_pattern)
            )
        ).limit(limit).all()
        
        return users
    
    @staticmethod
    def blacklist_token(jti, user_id, expires_at):
        """
        Add JWT token to blacklist
        
        Args:
            jti: JWT token ID
            user_id: User ID
            expires_at: Token expiration datetime
            
        Returns:
            BlacklistedToken: Created blacklist entry
        """
        blacklisted = BlacklistedToken(
            jti=jti,
            user_id=user_id,
            expires_at=expires_at
        )
        db.session.add(blacklisted)
        db.session.commit()
        
        logger.info(f"Token blacklisted for user: {user_id}")
        return blacklisted
