from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_marshmallow import Marshmallow
from flask_socketio import SocketIO
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
from datetime import datetime
from sqlalchemy import event
from sqlalchemy.engine import Engine
import time
import os
import logging

# Initialize extensions (but don't bind to app yet)
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
ma = Marshmallow()
socketio = SocketIO()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Cache will be initialized in create_app
cache = None

def setup_query_monitoring(app):
    """
    Setup database query performance monitoring.
    
    Monitors all database queries and logs slow queries (>100ms) with warnings.
    This helps identify N+1 query problems and performance bottlenecks.
    
    Only enabled when SQLALCHEMY_RECORD_QUERIES is True in config.
    """
    logger = logging.getLogger(__name__)
    
    # Only enable in development or when explicitly configured
    if app.config.get('SQLALCHEMY_RECORD_QUERIES', False):
        
        @event.listens_for(Engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            """Record query start time"""
            conn.info.setdefault('query_start_time', []).append(time.time())
        
        @event.listens_for(Engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            """Calculate query execution time and log slow queries"""
            try:
                total = time.time() - conn.info['query_start_time'].pop(-1)
                
                # Log slow queries (>100ms)
                if total > 0.1:
                    # Clean up the SQL statement for logging
                    clean_statement = ' '.join(statement.split())
                    if len(clean_statement) > 200:
                        clean_statement = clean_statement[:200] + '...'
                    
                    logger.warning(
                        f"Slow query detected ({total:.3f}s): {clean_statement}"
                    )
                
                # Log very slow queries (>1s) as errors
                if total > 1.0:
                    logger.error(
                        f"VERY SLOW QUERY ({total:.3f}s): {statement[:150]}..."
                    )
            except (IndexError, KeyError):
                # Handle edge case where timing info is missing
                pass
        
        app.logger.info("Database query performance monitoring enabled")
    else:
        app.logger.info("Database query performance monitoring disabled (set SQLALCHEMY_RECORD_QUERIES=True to enable)")

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
    ma.init_app(app)
    
    # Initialize rate limiter - DISABLE in debug mode for development
    # Rate limiting is important for production to prevent abuse, but annoying during development
    if app.config.get('DEBUG', False) or app.config.get('FLASK_DEBUG', False):
        app.logger.info("Rate limiting DISABLED (Debug mode enabled)")
        limiter.enabled = False
    else:
        app.logger.info("Rate limiting ENABLED (Production mode)")
    
    limiter.init_app(app)
    
    # Initialize caching
    global cache
    from app.utils.cache import init_cache
    cache = init_cache(app)
    app.logger.info(f"Cache initialized: {app.config.get('CACHE_TYPE', 'unknown')}")
    
    # Setup logging system (must be done before other initializations)
    from app.utils.logger import setup_logger
    setup_logger(app)
    
    # Setup database query performance monitoring
    setup_query_monitoring(app)
    
    # Initialize CORS for HTTP requests
    # Allow all origins for now - can be restricted in production if needed
    cors_origins = app.config.get('CORS_ORIGINS', '*')
    CORS(app, 
         origins=cors_origins,
         supports_credentials=True,
         allow_headers=['Content-Type', 'Authorization', 'X-Requested-With'],
         methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'PATCH', 'HEAD'],
         max_age=3600)  # Cache preflight for 1 hour
    app.logger.info(f"CORS enabled with origins: {cors_origins}")
    
    # Register request/response logging middleware
    from app.middleware import log_request, log_response
    app.before_request(log_request)
    app.after_request(log_response)
    
    # Add additional detailed logging for POST requests to debug Azure issues
    @app.before_request
    def log_post_requests():
        """Log detailed info for POST requests to debug Azure Container Apps issues"""
        if request.method in ['POST', 'PUT', 'PATCH']:
            app.logger.info(f"📥 POST REQUEST DETECTED: {request.method} {request.path}")
            app.logger.info(f"   Remote: {request.remote_addr}")
            app.logger.info(f"   Content-Type: {request.headers.get('Content-Type')}")
            app.logger.info(f"   Content-Length: {request.headers.get('Content-Length')}")
            try:
                body_preview = request.get_data(as_text=True)[:500]
                app.logger.info(f"   Body preview: {body_preview}")
            except Exception as e:
                app.logger.info(f"   Body: (could not read: {e})")
    
    # Initialize Socket.IO (single server mode - no Redis)
    cors_allowed = app.config.get('SOCKETIO_CORS_ALLOWED_ORIGINS', "*")
    async_mode = app.config.get('SOCKETIO_ASYNC_MODE', 'gevent')
    
    app.logger.info("Initializing Socket.IO (single server mode)")
    socketio.init_app(app, 
                     async_mode=async_mode,
                     cors_allowed_origins=cors_allowed,
                     logger=True,
                     engineio_logger=True)
    app.logger.info("Socket.IO initialized successfully")
    
    # Register blueprints (route modules)
    register_blueprints(app)
    
    # Register socket events
    register_socket_events(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register JWT handlers
    register_jwt_handlers(app)

    # Register health checks
    register_health_routes(app)
    
    # Register CLI commands
    register_cli_commands(app)
    
    # Register static file serving
    register_static_routes(app)

    # Initialize S3 service
    initialize_s3_service(app)

    # Note: No need to create local upload folders - all photos stored in S3!
    # The UPLOAD_FOLDER config exists for backward compatibility but isn't used
    
    return app

def register_blueprints(app):
    """Register all route blueprints"""
    
    # TODO: Create these route files later
    # For now, comment out to test models first
    
    # Import blueprints
    from app.routes.auth import auth_bp
    from app.routes.users import users_bp  
    from app.routes.dogs import dogs_bp
    from app.routes.matches import matches_bp
    from app.routes.messages import messages_bp
    from app.routes.events import events_bp
    from app.routes.migrate import migrate_bp
    from app.routes.s3 import s3_bp
    from app.routes.ai_assistant import ai_bp
    from app.routes.health import health_bp
    
    # Register with URL prefixes
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(dogs_bp, url_prefix='/api/dogs')
    app.register_blueprint(matches_bp, url_prefix='/api/matches')
    app.register_blueprint(messages_bp, url_prefix='/api/messages')
    app.register_blueprint(events_bp, url_prefix='/api/events')
    app.register_blueprint(migrate_bp, url_prefix='/api/migrate')
    app.register_blueprint(s3_bp, url_prefix='/api/s3')
    app.register_blueprint(ai_bp, url_prefix='/api/ai')
    app.register_blueprint(health_bp, url_prefix='/api')
    
def register_socket_events(app):
    """Register Socket.IO event handlers"""
    # Import socket events to register them
    from app.sockets import chat_events

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
        return BlacklistedToken.is_blacklisted(jti)
    
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

def register_cli_commands(app):
    """Register Flask CLI commands"""
    
    @app.cli.command("cleanup-blacklist")
    def cleanup_blacklist():
        """Remove expired tokens from blacklist"""
        from app.models.user import BlacklistedToken
        from datetime import datetime
        
        expired_count = BlacklistedToken.query.filter(
            BlacklistedToken.expires_at < datetime.utcnow()
        ).delete()
        db.session.commit()
        
        app.logger.info(f"Removed {expired_count} expired tokens from blacklist")
        print(f"✅ Removed {expired_count} expired tokens from blacklist")
    
    @app.cli.command("create-admin")
    def create_admin():
        """Create admin user for DogMatch application"""
        from app.models.user import User
        
        print("=" * 60)
        print("Creating Admin User for DogMatch")
        print("=" * 60)
        
        try:
            # Check if admin already exists
            existing_admin = User.query.filter_by(email='admin@dogmatch.com').first()
            if existing_admin:
                print("\n⚠️  Admin user already exists!")
                print(f"   Email: {existing_admin.email}")
                print(f"   Username: {existing_admin.username}")
                print(f"   User Type: {existing_admin.user_type}")
                return
            
            # Create admin user
            print("\n📝 Creating admin user...")
            admin = User(
                email='admin@dogmatch.com',
                password='Admin123!',
                username='admin',
                user_type='admin',
                first_name='Admin',
                last_name='DogMatch',
                phone='+1234567890',
                city='San Francisco',
                state='California',
                country='USA',
                is_active=True,
                is_verified=True
            )
            
            db.session.add(admin)
            db.session.commit()
            
            print("✅ Admin user created successfully!")
            print("\n" + "=" * 60)
            print("Admin User Credentials")
            print("=" * 60)
            print(f"Email:    admin@dogmatch.com")
            print(f"Password: Admin123!")
            print(f"Username: admin")
            print(f"Type:     admin")
            print("=" * 60)
            print("\n🎉 You can now login with these credentials!")
            print("   Use this account to create events and manage the app.")
            
        except Exception as e:
            print(f"\n❌ Error creating admin user!")
            print(f"Error: {str(e)}")
            db.session.rollback()
    
    @app.cli.command("test-db")
    def test_db():
        """Test database connection and display table information"""
        from app.models.user import User, BlacklistedToken
        from app.models.dog import Dog, Photo
        from app.models.event import Event
        from app.models.event_registration import EventRegistration
        from app.models.match import Match
        from app.models.message import Message
        
        print("=" * 60)
        print("Testing Database Connection")
        print("=" * 60)
        
        try:
            # Test database connection
            print("\n🔌 Testing database connection...")
            db.engine.connect()
            print("✅ Database connection successful!")
            
            # Get table names
            print("\n📋 Checking database tables...")
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            print(f"✅ Found {len(tables)} tables:")
            for table in sorted(tables):
                print(f"   - {table}")
            
            # Verify models can be queried
            print("\n🔍 Testing model queries...")
            
            models_to_test = [
                ('User', User),
                ('Dog', Dog),
                ('Event', Event),
                ('Match', Match),
                ('Message', Message),
                ('EventRegistration', EventRegistration),
                ('Photo', Photo),
                ('BlacklistedToken', BlacklistedToken)
            ]
            
            for model_name, model_class in models_to_test:
                try:
                    count = model_class.query.count()
                    print(f"   ✅ {model_name}: {count} records")
                except Exception as e:
                    print(f"   ❌ {model_name}: Error - {str(e)}")
            
            print("\n" + "=" * 60)
            print("✅ Database test PASSED")
            print("=" * 60)
            print("\n🎉 Your database is ready to use!")
            
        except Exception as e:
            print(f"\n❌ Database test failed!")
            print(f"Error: {str(e)}")
            print("\n" + "=" * 60)
            print("❌ Database test FAILED")
            print("=" * 60)

def register_health_routes(app):
    """Register health check routes"""

    from app.models.user import User

    @app.route('/', methods=['GET', 'HEAD'])
    def root():
        """Root endpoint for health checks"""
        return jsonify({
            'message': 'DogMatch API is running successfully',
            'status': 'healthy',
            'version': '1.0.0',
            'service': 'DogMatch Backend',
            'endpoints': {
                'auth': '/api/auth',
                'users': '/api/users', 
                'dogs': '/api/dogs',
                'matches': '/api/matches',
                'messages': '/api/messages',
                'events': '/api/events',
                's3': '/api/s3'
            },
            'documentation': {
                'health': '/',
                'user_registration': '/api/auth/register',
                'user_login': '/api/auth/login'
            }
        }), 200

    @app.route('/health', methods=['GET'])
    def health_check():
        """Detailed health check endpoint"""
        # Test database connection
        db_status = 'connected'
        try:
            User.query.first()  
        except Exception as e:
            db_status = f'error: {str(e)}'

        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'service': 'DogMatch Backend API',
            'version': '1.0.0',
            'database': db_status,
            'environment': app.config.get('FLASK_ENV', 'unknown'),
            'features': {
                'authentication': 'JWT + 2FA',
                'database': 'MySQL',
                'features': ['user_management', 'dog_profiles', 'matching', 'messaging', 'events']
            }
        }), 200

def register_static_routes(app):
    """Register static file serving routes"""
    
    from flask import send_from_directory
    import os
    
    @app.route('/static/dog_photos/<filename>')
    def uploaded_file(filename):
        """Serve uploaded dog photos"""
        # Get absolute path to upload folder
        upload_folder = os.path.abspath(app.config['UPLOAD_FOLDER'])
        file_path = os.path.join(upload_folder, filename)
        
        app.logger.debug(f"Static file request: {filename}")
        app.logger.debug(f"Upload folder: {upload_folder}")
        app.logger.debug(f"File path: {file_path}")
        app.logger.debug(f"File exists: {os.path.exists(file_path)}")
        
        if not os.path.exists(file_path):
            app.logger.warning(f"File not found: {file_path}")
            return "File not found", 404
            
        return send_from_directory(upload_folder, filename)

def initialize_s3_service(app):
    """Initialize S3 service for the app"""
    with app.app_context():
        from app.services.s3_service import s3_service
        # The s3_service will be initialized when imported
        app.logger.info("S3 service initialized")
