import os
from datetime import timedelta
from dotenv import load_dotenv

# Load variables
load_dotenv()

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")
    
    # Database Configuration - use DATABASE_URL directly from environment
    # Azure Web App for Containers provides DATABASE_URL directly
    db_url = os.environ.get("DATABASE_URL")
    if db_url and '?' in db_url:
        # Remove SSL parameters from DATABASE_URL if present
        db_url = db_url.split('?')[0]
    
    # Use DATABASE_URL directly (required for Azure deployment)
    # Fallback to individual components only for local development
    if db_url:
        SQLALCHEMY_DATABASE_URI = db_url
    else:
        # Fallback for local development (not used in Azure)
        SQLALCHEMY_DATABASE_URI = \
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
    
    # Cache Configuration (SimpleCache only - in-memory)
    CACHE_TYPE = "SimpleCache"
    CACHE_DEFAULT_TIMEOUT = int(os.environ.get("CACHE_DEFAULT_TIMEOUT", 300))  # 5 minutes default
    CACHE_KEY_PREFIX = "dogmatch:"
    
    # Socket.IO Configuration (single server mode - no Redis)
    SOCKETIO_CORS_ALLOWED_ORIGINS = "*"  # Allow all origins for Socket.IO
    
    # CORS Configuration for HTTP requests
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*")  # Allow all origins by default
    
class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False
    SQLALCHEMY_ECHO = True # Send queries to cli
    

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    SQLALCHEMY_ECHO = False
    
    PREFERRED_URL_SCHEME = "https"
    
    # Production Cache - use SimpleCache (in-memory)
    CACHE_DEFAULT_TIMEOUT = 600  # 10 minutes in production
    
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