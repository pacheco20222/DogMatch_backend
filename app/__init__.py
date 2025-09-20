from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_marshmallow import Marshmallow
import os

# Initialize extensions (but don't bind to app yet)
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
cors = CORS()
ma = Marshmallow()

def create_app(config_name=None):
    """
    Application Factory Pattern
    Creates and configures the Flask application instance
    """
    
    # Create Flask app instance
    app = Flask(__name__)
    
    # Load configuration
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    from app.config import config
    app.config.from_object(config[config_name])
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app, origins=app.config['CORS_ORIGINS'])
    ma.init_app(app)
    
    # Import models (needed for migrations) - import after app context is created
    with app.app_context():
        from app.models import user, dog, match, message, event, event_registration
    
    # Register blueprints (route modules)
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register JWT handlers
    register_jwt_handlers(app)
    
    # Create upload folder if it doesn't exist
    upload_folder = app.config['UPLOAD_FOLDER']
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder, exist_ok=True)
    
    return app

def register_blueprints(app):
    """Register all route blueprints"""
    
    # TODO: Create these route files later
    # For now, comment out to test models first
    
    # Import blueprints
    # from app.routes.auth import auth_bp
    # from app.routes.users import users_bp  
    # from app.routes.dogs import dogs_bp
    # from app.routes.matches import matches_bp
    # from app.routes.messages import messages_bp
    # from app.routes.events import events_bp
    
    # Register with URL prefixes
    # app.register_blueprint(auth_bp, url_prefix='/api/auth')
    # app.register_blueprint(users_bp, url_prefix='/api/users')
    # app.register_blueprint(dogs_bp, url_prefix='/api/dogs')
    # app.register_blueprint(matches_bp, url_prefix='/api/matches')
    # app.register_blueprint(messages_bp, url_prefix='/api/messages')
    # app.register_blueprint(events_bp, url_prefix='/api/events')
    
    pass  # No routes for now

def register_error_handlers(app):
    """Register global error handlers"""
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'error': 'Bad Request',
            'message': 'The request could not be understood by the server'
        }), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({
            'error': 'Unauthorized',
            'message': 'Authentication required'
        }), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({
            'error': 'Forbidden',
            'message': 'You do not have permission to access this resource'
        }), 403
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'error': 'Not Found',
            'message': 'The requested resource was not found'
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred'
        }), 500

def register_jwt_handlers(app):
    """Register JWT-related handlers"""
    
    # Import here to avoid circular imports
    from app.models.user import BlacklistedToken
    
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        """Check if JWT token is blacklisted (revoked)"""
        jti = jwt_payload['jti']  # JWT ID - unique identifier for each token
        blacklisted_token = BlacklistedToken.query.filter_by(jti=jti).first()
        return blacklisted_token is not None
    
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        """Called when token has expired"""
        return jsonify({
            'error': 'Token Expired',
            'message': 'The JWT token has expired'
        }), 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        """Called when token is invalid"""
        return jsonify({
            'error': 'Invalid Token',
            'message': 'The JWT token is invalid'
        }), 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        """Called when no token is provided"""
        return jsonify({
            'error': 'Missing Token',
            'message': 'JWT token is required for this endpoint'
        }), 401
    
    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        """Called when token is blacklisted"""
        return jsonify({
            'error': 'Revoked Token',
            'message': 'The JWT token has been revoked'
        }), 401