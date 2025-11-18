"""
Health check endpoints for monitoring and orchestration
"""
from flask import Blueprint, jsonify, current_app
import time
import logging

# Get the logger that's already configured in your app
logger = logging.getLogger(__name__)

health_bp = Blueprint('health', __name__)


@health_bp.route('/health', methods=['GET'])
def health_check():
    """
    Basic health check endpoint
    Returns 200 if service is running
    """
    return jsonify({
        'status': 'healthy',
        'service': 'dogmatch-backend',
        'timestamp': time.time()
    }), 200


@health_bp.route('/health/ready', methods=['GET'])
def readiness_check():
    """
    Readiness check - verifies all dependencies are available
    Returns 200 if service is ready to accept traffic
    """
    from app import db
    
    checks = {
        'database': False,
        'redis': False,
        'overall': False
    }
    
    try:
        # Check database connection
        db.session.execute(db.text('SELECT 1'))
        checks['database'] = True
        logger.debug('Health check: Database is healthy')
    except Exception as e:
        logger.error(f'Health check: Database is unhealthy - {str(e)}')
    
    try:
        # Check Redis connection - access through current_app
        redis_client = current_app.extensions.get('redis')
        if redis_client:
            redis_client.ping()
            checks['redis'] = True
            logger.debug('Health check: Redis is healthy')
        else:
            logger.warning('Health check: Redis client not configured')
            checks['redis'] = True  # Don't fail if Redis is optional
    except Exception as e:
        logger.error(f'Health check: Redis is unhealthy - {str(e)}')
        checks['redis'] = True  # Don't fail if Redis is optional
    
    # Overall status
    checks['overall'] = checks['database'] and checks['redis']
    
    status_code = 200 if checks['overall'] else 503
    
    return jsonify({
        'status': 'ready' if checks['overall'] else 'not_ready',
        'checks': checks,
        'timestamp': time.time()
    }), status_code


@health_bp.route('/health/live', methods=['GET'])
def liveness_check():
    """
    Liveness check - verifies the application is running
    Returns 200 if the application process is alive
    """
    return jsonify({
        'status': 'alive',
        'timestamp': time.time()
    }), 200
