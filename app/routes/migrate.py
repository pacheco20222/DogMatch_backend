# /app/routes/migrate.py
from flask import Blueprint, jsonify, current_app
from flask_migrate import upgrade, init, migrate, current, revision
from app import db

migrate_bp = Blueprint("migrate", __name__)

@migrate_bp.route('/init', methods=['POST'])
def init_database():
    """
    Initialize database tables
    POST /api/migrate/init
    """
    try:
        # Create all tables
        db.create_all()
        
        return jsonify({
            'message': 'Database tables created successfully',
            'status': 'success'
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Database initialization failed: {e}")
        return jsonify({
            'error': 'Database initialization failed',
            'message': str(e)
        }), 500

@migrate_bp.route('/status', methods=['GET'])
def migration_status():
    """
    Check migration status
    GET /api/migrate/status
    """
    try:
        # Check if tables exist by trying to query a simple table
        from app.models import User
        user_count = User.query.count()
        
        return jsonify({
            'message': 'Database is initialized',
            'status': 'success',
            'user_count': user_count
        }), 200
        
    except Exception as e:
        return jsonify({
            'message': 'Database not initialized',
            'status': 'error',
            'error': str(e)
        }), 200
