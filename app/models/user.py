# # app/models/user.py
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from app import db
import pyotp
import qrcode
import io
import base64
import secrets
import string

class User(db.Model):
    """
    User model for DogMatch application
    Handles owners, shelters, and administrators with 2FA support
    """
    
    # Table configuration
    __tablename__ = 'users'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Authentication fields
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Two-Factor Authentication fields
    totp_secret = db.Column(db.String(32), nullable=True)  # TOTP secret key
    is_2fa_enabled = db.Column(db.Boolean, default=False, nullable=False)
    backup_codes = db.Column(db.Text, nullable=True)  # JSON array of backup codes
    last_totp_used = db.Column(db.Integer, nullable=True)  # Prevent TOTP replay attacks
    
    # Profile fields
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    first_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    
    # User type field - determines permissions
    user_type = db.Column(db.Enum('owner', 'shelter', 'admin', name='user_type_enum'), 
                         nullable=False, default='owner')
    
    # Location fields
    city = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(100), nullable=True)
    country = db.Column(db.String(100), nullable=True, default='Mexico')
    
    # Profile photo fields (for S3 integration)
    profile_photo_url = db.Column(db.String(500), nullable=True)  # S3 URL for profile photo
    profile_photo_filename = db.Column(db.String(255), nullable=True)  # Original filename
    
    # Account status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    
    # Login attempt tracking (security)
    failed_login_attempts = db.Column(db.Integer, default=0, nullable=False)
    locked_until = db.Column(db.DateTime, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)
    
    # Relationships (will be populated when we create other models)
    dogs = db.relationship('Dog', backref='owner', lazy=True, cascade='all, delete-orphan')
    organized_events = db.relationship('Event', backref='organizer', lazy=True, cascade='all, delete-orphan')
    event_registrations = db.relationship('EventRegistration', 
                                    foreign_keys='EventRegistration.user_id',
                                    backref='user', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, email, password, username, user_type='owner', **kwargs):
        """
        Initialize User instance
        Automatically hashes password
        """
        self.email = email.lower().strip()  # Normalize email
        self.username = username.strip()
        self.user_type = user_type
        self.set_password(password)
        
        # Set optional fields
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def set_password(self, password):
        """
        Hash and store password
        Uses Werkzeug's secure password hashing
        """
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)
    
    def check_password(self, password):
        """
        Verify password against stored hash
        Returns True if password matches, False otherwise
        """
        return check_password_hash(self.password_hash, password)
    
    def is_account_locked(self):
        """Check if account is temporarily locked due to failed login attempts"""
        if self.locked_until and datetime.utcnow() < self.locked_until:
            return True
        return False
    
    def increment_failed_login(self):
        """Increment failed login attempts and lock account if necessary"""
        self.failed_login_attempts += 1
        
        # Lock account for 15 minutes after 5 failed attempts
        if self.failed_login_attempts >= 5:
            self.locked_until = datetime.utcnow() + timedelta(minutes=15)
        
        db.session.commit()
    
    def reset_failed_login(self):
        """Reset failed login attempts after successful login"""
        self.failed_login_attempts = 0
        self.locked_until = None
        db.session.commit()
    
    def update_last_login(self):
        """Update the last_login timestamp and reset failed attempts"""
        self.last_login = datetime.utcnow()
        self.reset_failed_login()
    
    # ========== TWO-FACTOR AUTHENTICATION METHODS ==========
    
    def generate_totp_secret(self):
        """Generate a new TOTP secret for 2FA setup"""
        self.totp_secret = pyotp.random_base32()
        return self.totp_secret
    
    def get_totp_uri(self):
        """Generate TOTP URI for QR code generation"""
        if not self.totp_secret:
            raise ValueError("TOTP secret not generated")
        
        return pyotp.totp.TOTP(self.totp_secret).provisioning_uri(
            name=self.email,
            issuer_name="DogMatch"
        )
    
    def generate_qr_code(self):
        """Generate QR code for TOTP setup"""
        if not self.totp_secret:
            raise ValueError("TOTP secret not generated")
        
        # Create QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(self.get_totp_uri())
        qr.make(fit=True)
        
        # Create QR code image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64 string
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_str = base64.b64encode(img_buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"
    
    def verify_totp(self, token):
        """
        Verify TOTP token
        Includes replay attack protection
        """
        if not self.totp_secret:
            return False
        
        totp = pyotp.TOTP(self.totp_secret)
        
        # Get current time window
        current_time = datetime.utcnow()
        time_window = int(current_time.timestamp()) // 30
        
        # Check if this time window was already used
        if self.last_totp_used and self.last_totp_used >= time_window:
            return False  # Prevent replay attacks
        
        # Verify the token (allows for clock skew)
        if totp.verify(token, valid_window=1):
            self.last_totp_used = time_window
            db.session.commit()
            return True
        
        return False
    
    def enable_2fa(self, totp_token):
        """
        Enable 2FA after verifying the initial TOTP token
        Also generates backup codes
        """
        if not self.totp_secret:
            raise ValueError("TOTP secret not generated")
        
        # Verify the token first
        if not self.verify_totp(totp_token):
            return False
        
        # Enable 2FA and generate backup codes
        self.is_2fa_enabled = True
        self.generate_backup_codes()
        db.session.commit()
        return True
    
    def disable_2fa(self):
        """Disable 2FA and clear related data"""
        self.is_2fa_enabled = False
        self.totp_secret = None
        self.backup_codes = None
        self.last_totp_used = None
        db.session.commit()
    
    def generate_backup_codes(self):
        """Generate 10 backup codes for 2FA recovery"""
        import json
        
        codes = []
        for _ in range(10):
            # Generate 8-character alphanumeric codes
            code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
            codes.append({
                'code': code,
                'used': False,
                'used_at': None
            })
        
        self.backup_codes = json.dumps(codes)
        return [code['code'] for code in codes]
    
    def verify_backup_code(self, code):
        """
        Verify and mark a backup code as used
        Returns True if valid, False otherwise
        """
        if not self.backup_codes:
            return False
        
        import json
        codes = json.loads(self.backup_codes)
        
        for backup_code in codes:
            if backup_code['code'] == code.upper() and not backup_code['used']:
                backup_code['used'] = True
                backup_code['used_at'] = datetime.utcnow().isoformat()
                self.backup_codes = json.dumps(codes)
                db.session.commit()
                return True
        
        return False
    
    def get_unused_backup_codes(self):
        """Get list of unused backup codes"""
        if not self.backup_codes:
            return []
        
        import json
        codes = json.loads(self.backup_codes)
        return [code['code'] for code in codes if not code['used']]
    
    def verify_2fa(self, token=None, backup_code=None):
        """
        Verify 2FA using either TOTP token or backup code
        """
        if not self.is_2fa_enabled:
            return True  # 2FA not enabled, so it's valid
        
        if token:
            return self.verify_totp(token)
        elif backup_code:
            return self.verify_backup_code(backup_code)
        
        return False
    
    # ========== OTHER USER METHODS ==========
    
    def get_full_name(self):
        """Return full name or username if names not provided"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        else:
            return self.username
    
    def get_profile_photo_url(self):
        """Get profile photo URL or default placeholder"""
        return self.profile_photo_url or '/static/images/default-user.jpg'
    
    def is_admin(self):
        """Check if user has admin privileges"""
        return self.user_type == 'admin'
    
    def is_shelter(self):
        """Check if user is a shelter/NGO"""
        return self.user_type == 'shelter'
    
    def is_owner(self):
        """Check if user is a regular dog owner"""
        return self.user_type == 'owner'
    
    def to_dict(self, include_sensitive=False, include_2fa_status=False):
        """
        Convert user to dictionary for JSON responses
        include_sensitive: Whether to include email and phone (admin only)
        include_2fa_status: Whether to include 2FA status information
        """
        def safe_isoformat(dt_obj):
            """Safely convert datetime to isoformat string"""
            if dt_obj is None:
                return None
            if hasattr(dt_obj, 'isoformat'):
                return dt_obj.isoformat()
            return str(dt_obj)
        
        # Generate signed URL for profile photo if S3 key exists
        profile_photo_url = None
        if self.profile_photo_url:
            # Check if it's an S3 key (starts with user-photos/) or already a URL
            if self.profile_photo_url.startswith('user-photos/'):
                # It's an S3 key - generate signed URL
                from app.services.s3_service import s3_service
                profile_photo_url = s3_service.get_photo_url(
                    self.profile_photo_url, 
                    signed=True, 
                    expiration=604800  # 7 days
                )
            else:
                # It's already a URL (legacy data or external URL)
                profile_photo_url = self.profile_photo_url
        
        data = {
            'id': self.id,
            'username': self.username,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.get_full_name(),
            'user_type': self.user_type,
            'city': self.city,
            'state': self.state,
            'country': self.country,
            'profile_photo_url': profile_photo_url,  # Fresh signed URL
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'created_at': safe_isoformat(self.created_at),
            'last_login': safe_isoformat(self.last_login)
        }
        
        if include_sensitive:
            data.update({
                'email': self.email,
                'phone': self.phone
            })
        
        if include_2fa_status:
            data.update({
                'is_2fa_enabled': self.is_2fa_enabled,
                'has_backup_codes': self.backup_codes is not None,
                'unused_backup_codes_count': len(self.get_unused_backup_codes())
            })
        
        return data
    
    def __repr__(self):
        """String representation for debugging"""
        return f'<User {self.username} ({self.user_type})>'


class BlacklistedToken(db.Model):
    """
    Model to store blacklisted JWT tokens
    Used for logout functionality and token revocation
    """
    
    __tablename__ = 'blacklisted_tokens'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    jti = db.Column(db.String(36), unique=True, nullable=False, index=True)  # JWT ID
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    token_type = db.Column(db.Enum('access', 'refresh', name='token_type_enum'), nullable=False)
    blacklisted_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)  # When token would have naturally expired
    
    # Relationship
    user = db.relationship('User', backref='blacklisted_tokens')
    
    def __init__(self, jti, user_id, token_type, expires_at):
        self.jti = jti
        self.user_id = user_id
        self.token_type = token_type
        self.expires_at = expires_at
    
    @staticmethod
    def is_blacklisted(jti):
        """Check if a token is blacklisted"""
        return BlacklistedToken.query.filter_by(jti=jti).first() is not None
    
    def __repr__(self):
        return f'<BlacklistedToken {self.jti}>'