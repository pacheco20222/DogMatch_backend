# app/utils/logger.py
"""
Centralized logging configuration for DogMatch backend
Replaces print statements with proper structured logging
"""

import logging
import sys
import os
from logging.handlers import RotatingFileHandler


def setup_logger(app):
    """
    Configure application logging with both console and file handlers
    
    Features:
    - Environment-based log levels (DEBUG in dev, INFO in prod)
    - Structured log format with timestamps and context
    - File rotation (10MB files, keep 10 backups)
    - Console output for development
    - Production-ready file logging
    
    Args:
        app: Flask application instance
    """
    # Set log level based on environment
    log_level = logging.DEBUG if app.debug else logging.INFO
    
    # Create formatter with structured format
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler (always enabled)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    
    # Clear any existing handlers to avoid duplicates
    app.logger.handlers.clear()
    
    # Add console handler
    app.logger.addHandler(console_handler)
    
    # File handler (only in production or when explicitly enabled)
    if not app.debug or os.getenv('ENABLE_FILE_LOGGING', 'false').lower() == 'true':
        # Create logs directory if it doesn't exist
        log_dir = os.path.join(os.path.dirname(app.root_path), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, 'dogmatch.log')
        
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10485760,  # 10MB
            backupCount=10
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        app.logger.info(f"File logging enabled: {log_file}")
    
    # Set the logger level
    app.logger.setLevel(log_level)
    
    # Log startup
    app.logger.info("=" * 50)
    app.logger.info("DogMatch Backend Starting")
    app.logger.info(f"Environment: {'Development' if app.debug else 'Production'}")
    app.logger.info(f"Log Level: {logging.getLevelName(log_level)}")
    app.logger.info("=" * 50)
    
    return app.logger
