import os
from datetime import timedelta
from dotenv import load_dotenv

# Load variables
load_dotenv()

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")
    
    # Database Configuration, to connect to the database
    # For AWS RDS, we need to handle SSL properly
    db_url = os.environ.get("DATABASE_URL")
    if db_url and '?' in db_url:
        # Remove SSL parameters from DATABASE_URL if present
        db_url = db_url.split('?')[0]
    
    SQLALCHEMY_DATABASE_URI = db_url or \
        f"mysql+pymysql://{os.environ.get('DB_USER')}:{os.environ.get('DB_PASSWORD')}@{os.environ.get('DB_HOST')}:{os.environ.get('DB_PORT', '3306')}/{os.environ.get('DB_NAME')}"
    
    # SQLAlchemy engine options for SSL
    SQLALCHEMY_ENGINE_OPTIONS = {
        'connect_args': {
            'ssl': {
                'ssl_disabled': False
            }
        }
    }
        
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True
    
    JWT_SECRET_KEY = os.environ.get("SECRET_KEY") or SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRES', 30)))
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=int(os.environ.get('JWT_REFRESH_TOKEN_EXPIRES', 7)))
    
    JWT_BLACKLIST_ENABLED = True
    JWT_BLACKLIST_TOKEN_CHECKS = ["access", "refresh"]
    
    # File Upload Settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = os.path.join('app', 'static', 'dog_photos')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    
    # CORS Configuration
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "").split(',')
    CORS_SUPPORTS_CREDENTIALS = True
    CORS_ALLOW_HEADERS = ['Content-Type', 'Authorization']
    CORS_EXPOSE_HEADERS = ['Content-Type', 'Authorization']
    CORS_MAX_AGE = 600  # Cache preflight requests for 10 minutes
    
    # Cache Configuration
    CACHE_TYPE = os.environ.get("CACHE_TYPE", "SimpleCache")  # SimpleCache, redis, or FileSystemCache
    CACHE_DEFAULT_TIMEOUT = int(os.environ.get("CACHE_DEFAULT_TIMEOUT", 300))  # 5 minutes default
    CACHE_KEY_PREFIX = "dogmatch:"
    # Redis configuration (used if CACHE_TYPE='redis')
    REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    
    # Socket.IO Configuration
    SOCKETIO_USE_REDIS = False  # Override in ProductionConfig
    
class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False
    SQLALCHEMY_ECHO = True # Send queries to cli
    
    # Development CORS - allow localhost
    CORS_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:19006"]
    
    # Development Cache - use SimpleCache (in-memory, no Redis needed)
    CACHE_TYPE = "SimpleCache"
    
    # Development Socket.IO - no Redis needed (single server)
    SOCKETIO_USE_REDIS = False
    

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    SQLALCHEMY_ECHO = False
    
    PREFERRED_URL_SCHEME = "https"
    
    # Production Cache - use Redis for distributed caching
    CACHE_TYPE = "redis"
    CACHE_DEFAULT_TIMEOUT = 600  # 10 minutes in production
    
    # Production Socket.IO - use Redis for horizontal scaling
    SOCKETIO_USE_REDIS = True
    
    # Production CORS - must be set via environment variable
    # Override parent class default
    def __init__(self):
        super().__init__()
        cors_origins = os.environ.get("CORS_ORIGINS", "")
        if not cors_origins or cors_origins.strip() == "":
            raise ValueError(
                "CORS_ORIGINS environment variable must be set in production! "
                "Example: CORS_ORIGINS='https://yourdomain.com,https://www.yourdomain.com'"
            )
        self.CORS_ORIGINS = [origin.strip() for origin in cors_origins.split(',') if origin.strip()]
    
class TestingConfig(Config):
    """Testing environment configuration"""
    DEBUG = True
    TESTING = True
    
    # Test Cache - use SimpleCache
    CACHE_TYPE = "SimpleCache"
    TESTING = True
    DEBUG = True
    
    # Use in-memory SQLite for faster testing
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    # Disable CSRF for testing
    WTF_CSRF_ENABLED = False

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}