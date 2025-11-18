# /app/routes/auth.py
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import (
    create_access_token, create_refresh_token, get_jwt_identity, 
    jwt_required, get_jwt, get_current_user
)
from marshmallow import ValidationError
from datetime import datetime, timedelta
import uuid

from app import db, limiter
from app.models.user import User, BlacklistedToken
from app.utils.sanitizer import sanitize_user_input
from app.schemas.user_schemas import (
    UserRegistrationSchema, UserLoginSchema, UserResponseSchema, 
    Setup2FASchema, Verify2FASchema
)


#And define the Blueprint
auth_bp = Blueprint("auth", __name__)

@auth_bp.route('/', methods=['GET', 'POST', 'OPTIONS'])
def root():
    """Root endpoint - also accepts POST/OPTIONS for testing"""
    if request.method == 'OPTIONS':
        # Handle CORS preflight
        return '', 200
    
    return jsonify({
        'message': 'DogMatch API is running',
        'version': '1.0.0',
        'status': 'healthy',
        'method': request.method,
        'endpoints': {
            'auth': '/api/auth',
            'users': '/api/users',
            'dogs': '/api/dogs',
            'matches': '/api/matches',
            'messages': '/api/messages',
            'events': '/api/events'
        }
    }), 200

@auth_bp.route('/register', methods=['POST'])
@limiter.limit("3 per hour")
def register():
    """
    Register a new user
    POST /api/auth/register
    Rate limit: 3 registrations per hour per IP
    """
    try:
        # Validate input data
        schema = UserRegistrationSchema()
        data = schema.load(request.json)
        
        # Sanitize text fields to prevent XSS attacks
        data = sanitize_user_input(data)
        
        # Create new user
        user = User(
            email=data['email'],
            password=data['password'],
            username=data['username'],
            user_type=data.get('user_type', 'owner'),
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            phone=data.get('phone'),
            city=data.get('city'),
            state=data.get('state'),
            country=data.get('country', 'Mexico'),
            profile_photo_url=data.get('profile_photo_url')
        )
        
        # Save to database
        db.session.add(user)
        db.session.commit()
        
        # Create tokens
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))
        
        # Return user data and tokens
        return jsonify({
            'message': 'User registered successfully',
            'user': user.to_dict(include_sensitive=True),
            'access_token': access_token,
            'refresh_token': refresh_token
        }), 201
        
    except ValidationError as e:
        return jsonify({
            'error': 'User could not be verified',
            'messages': e.messages
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'Failed to register the user',
            'message': str(e)
        }), 500
        
@auth_bp.route('/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    """
    Login user with email/password and optional 2FA
    POST /api/auth/login
    Rate limit: 5 login attempts per minute per IP
    """
    try:
        # Validate input data
        schema = UserLoginSchema()
        data = schema.load(request.json)
        
        # Find user by email
        user = User.query.filter_by(email=data['email'].lower()).first()
        if not user:
            return jsonify({
                'error': 'Invalid credentials',
                'message': 'Email or password is incorrect'
            }), 401
        
        # Check if account is locked
        if user.is_account_locked():
            return jsonify({
                'error': 'Account locked',
                'message': 'Account is temporarily locked due to failed login attempts'
            }), 423
        
        # Check password
        if not user.check_password(data['password']):
            user.increment_failed_login()
            return jsonify({
                'error': 'Invalid credentials',
                'message': 'Email or password is incorrect'
            }), 401
        
        # Check if account is active
        if not user.is_active:
            return jsonify({
                'error': 'Account disabled',
                'message': 'Your account has been disabled'
            }), 403
        
        # Handle 2FA if enabled
        if user.is_2fa_enabled:
            totp_token = data.get('totp_token')
            backup_code = data.get('backup_code')
            
            if not totp_token and not backup_code:
                return jsonify({
                    'error': '2FA required',
                    'message': 'Please provide TOTP token or backup code',
                    'requires_2fa': True
                }), 200 
            
            # Verify 2FA
            if not user.verify_2fa(token=totp_token, backup_code=backup_code):
                user.increment_failed_login()
                return jsonify({
                    'error': 'Invalid 2FA code',
                    'message': 'TOTP token or backup code is invalid'
                }), 401
        
        user.update_last_login()
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))
        
        # Return user data and tokens
        
        return jsonify({
            'message': 'Login successful',
            'user': user.to_dict(include_sensitive=True),
            'access_token': access_token,
            'refresh_token': refresh_token
        }), 200
        
    except ValidationError as e:
        return jsonify({
            'error': 'Validation failed',
            'messages': e.messages
        }), 400
    except Exception as e:
        return jsonify({
            'error': 'Login failed',
            'message': str(e)
        }), 500

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """
    Refresh access token using refresh token
    POST /api/auth/refresh
    """
    try:
        current_user_id = int(get_jwt_identity())
        user = User.query.get(current_user_id)
        
        if not user or not user.is_active:
            return jsonify({
                'error': 'Invalid user',
                'message': 'User not found or account disabled'
            }), 401
        
        # Create new access token
        new_access_token = create_access_token(identity=current_user_id)
        
        return jsonify({
            'access_token': new_access_token
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': 'Token refresh failed',
            'message': str(e)
        }), 500

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """
    Logout user by blacklisting their current JWT token
    POST /api/auth/logout
    """
    try:
        # Get JWT data
        jwt_data = get_jwt()
        jti = jwt_data['jti']  # JWT ID - unique identifier
        user_id = int(get_jwt_identity())
        token_type = jwt_data.get('type', 'access')
        
        # Calculate token expiration
        exp_timestamp = jwt_data['exp']
        expires_at = datetime.fromtimestamp(exp_timestamp)
        
        # Add token to blacklist
        blacklisted_token = BlacklistedToken(
            jti=jti,
            user_id=user_id,
            token_type=token_type,
            expires_at=expires_at
        )
        db.session.add(blacklisted_token)
        db.session.commit()
        
        current_app.logger.info(f"User {user_id} logged out, token {jti} blacklisted")
        
        return jsonify({
            'message': 'Successfully logged out'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Logout failed: {str(e)}")
        return jsonify({
            'error': 'Logout failed',
            'message': str(e)
        }), 500
        
@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    try:
        from flask import current_app
        current_user_id = int(get_jwt_identity())  # Convert string back to int
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        current_app.logger.info(f"📸 /api/auth/me - user.profile_photo_url from DB: {user.profile_photo_url}")
        
        user_dict = user.to_dict(include_sensitive=True, include_2fa_status=True)
        current_app.logger.info(f"📸 /api/auth/me - returning profile_photo_url: {user_dict.get('profile_photo_url')}")
        
        return jsonify({
            'user': user_dict
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to get user profile',
            'message': str(e)
        }), 500
        
@auth_bp.route('/2fa/setup', methods=['POST'])
@jwt_required()
def setup_2fa():
    """
    Generate QR code for 2FA setup
    POST /api/auth/2fa/setup
    """
    try:
        current_user_id = int(get_jwt_identity())
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if user.is_2fa_enabled:
            return jsonify({
                'error': '2FA already enabled',
                'message': 'Two-factor authentication is already enabled for this account'
            }), 400
        
        secret = user.generate_totp_secret()
        
        qr_code = user.generate_qr_code()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Scan the QR code with your authenticator app',
            'qr_code': qr_code,
            'secret': secret,  # For typing in the code
            'totp_uri': user.get_totp_uri()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': '2FA setup failed',
            'message': str(e)
        }), 500
        
@auth_bp.route('/2fa/enable', methods=['POST'])
@jwt_required()
def enable_2fa():
    """
    Enable 2FA after verifying TOTP token
    POST /api/auth/2fa/enable
    """
    try:
        # Validate input
        schema = Setup2FASchema()
        data = schema.load(request.json)
        
        current_user_id = int(get_jwt_identity())
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if user.is_2fa_enabled:
            return jsonify({
                'error': '2FA already enabled'
            }), 400
        
        if not user.totp_secret:
            return jsonify({
                'error': 'No 2FA setup found',
                'message': 'Please setup 2FA first using /auth/2fa/setup'
            }), 400
        
        # Enable 2FA with token verification
        if user.enable_2fa(data['totp_token']):
            backup_codes = user.get_unused_backup_codes()
            
            return jsonify({
                'message': '2FA enabled successfully',
                'backup_codes': backup_codes
            }), 200
        else:
            return jsonify({
                'error': 'Invalid TOTP token',
                'message': 'Please check your authenticator app and try again'
            }), 400
            
    except ValidationError as e:
        return jsonify({
            'error': 'Validation failed',
            'messages': e.messages
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': '2FA enable failed',
            'message': str(e)
        }), 500
        
@auth_bp.route('/2fa/disable', methods=['POST'])
@jwt_required()
def disable_2fa():
    """
    Disable 2FA for current user
    POST /api/auth/2fa/disable
    """
    try:
        # Validate TOTP token to confirm identity
        schema = Verify2FASchema()
        data = schema.load(request.json)
        
        current_user_id = int(get_jwt_identity())
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if not user.is_2fa_enabled:
            return jsonify({
                'error': '2FA not enabled'
            }), 400
        
        # Verify identity with 2FA before disabling
        totp_token = data.get('totp_token')
        backup_code = data.get('backup_code')
        
        if not user.verify_2fa(token=totp_token, backup_code=backup_code):
            return jsonify({
                'error': 'Invalid 2FA code',
                'message': 'Please provide valid TOTP token or backup code'
            }), 401
        
        # Disable 2FA
        user.disable_2fa()
        
        return jsonify({
            'message': '2FA disabled successfully'
        }), 200
        
    except ValidationError as e:
        return jsonify({
            'error': 'Validation failed',
            'messages': e.messages
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': '2FA disable failed',
            'message': str(e)
        }), 500


@auth_bp.route('/2fa/backup-codes', methods=['POST'])
@jwt_required()
def regenerate_backup_codes():
    """
    Generate new backup codes (invalidates old ones)
    POST /api/auth/2fa/backup-codes
    """
    try:
        current_user_id = int(get_jwt_identity())
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if not user.is_2fa_enabled:
            return jsonify({
                'error': '2FA not enabled'
            }), 400
        
        # Generate new backup codes
        backup_codes = user.generate_backup_codes()
        db.session.commit()
        
        return jsonify({
            'message': 'New backup codes generated',
            'backup_codes': backup_codes,
            'warning': 'Old backup codes have been invalidated'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'Backup code generation failed',
            'message': str(e)
        }), 500
        
@auth_bp.route('/debug-token', methods=['POST'])
def debug_token():
    """Debug token generation and validation"""
    try:
        # Create a simple test token
        test_token = create_access_token(identity="999")
        
        return jsonify({
            'test_token': test_token,
            'jwt_secret_key': current_app.config.get('JWT_SECRET_KEY', 'NOT_SET'),
            'secret_key': current_app.config.get('SECRET_KEY', 'NOT_SET')
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': 'Token debug failed',
            'message': str(e)
        }), 500
        
@auth_bp.route('/test-jwt', methods=['GET'])
@jwt_required(verify_type=False)  # Skip some validations for testing
def test_jwt():
    """Test basic JWT functionality"""
    try:
        current_user_id = int(get_jwt_identity())
        claims = get_jwt()
        
        return jsonify({
            'message': 'JWT validation successful',
            'user_id': current_user_id,
            'jti': claims.get('jti'),
            'token_type': claims.get('type')
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': 'JWT test failed',
            'message': str(e)
        }), 500
        
@auth_bp.route('/jwt-minimal-test', methods=['GET'])
def jwt_minimal_test():
    """Minimal JWT test without decorators"""
    try:
        from flask_jwt_extended import decode_token
        
        # Get token from Authorization header manually
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'No token provided'}), 401
            
        token = auth_header.split(' ')[1]
        
        # Try to decode the token manually
        decoded = decode_token(token)
        
        return jsonify({
            'message': 'Token decoded successfully',
            'decoded_token': decoded
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': 'Token decode failed',
            'message': str(e),
            'error_type': type(e).__name__
        }), 500