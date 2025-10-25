"""
Request/Response Logging Middleware

Provides centralized logging for all API requests and responses,
including timing information, status codes, and remote addresses.
"""

from flask import request, g
from time import time
import logging

logger = logging.getLogger(__name__)


def log_request():
    """
    Log incoming requests before processing.
    
    Records:
    - HTTP method (GET, POST, etc.)
    - Request path
    - Remote IP address
    - Query parameters (if any)
    - User agent
    
    Also stores start time in Flask's g object for response timing.
    """
    g.start_time = time()
    
    # Build log message
    log_msg = f"{request.method} {request.path}"
    
    # Add query parameters if present
    if request.query_string:
        log_msg += f"?{request.query_string.decode('utf-8')}"
    
    # Add remote address
    log_msg += f" - {request.remote_addr}"
    
    # Add user agent for debugging
    user_agent = request.headers.get('User-Agent', 'Unknown')
    if user_agent and user_agent != 'Unknown':
        log_msg += f" - {user_agent[:50]}"  # Truncate long user agents
    
    logger.info(log_msg)


def log_response(response):
    """
    Log outgoing responses after processing.
    
    Records:
    - HTTP method and path
    - Response status code
    - Processing time (elapsed seconds)
    - Response size (if available)
    
    Args:
        response: Flask response object
        
    Returns:
        response: Unmodified Flask response object
    """
    if hasattr(g, 'start_time'):
        elapsed = time() - g.start_time
        
        # Build log message
        log_msg = (
            f"{request.method} {request.path} - "
            f"Status: {response.status_code} - "
            f"Time: {elapsed:.3f}s"
        )
        
        # Add response size if available
        if response.content_length:
            size_kb = response.content_length / 1024
            log_msg += f" - Size: {size_kb:.2f}KB"
        
        # Use different log levels based on status code
        if response.status_code >= 500:
            logger.error(log_msg)
        elif response.status_code >= 400:
            logger.warning(log_msg)
        elif elapsed > 1.0:  # Slow request warning
            logger.warning(f"{log_msg} [SLOW REQUEST]")
        else:
            logger.info(log_msg)
    
    return response
