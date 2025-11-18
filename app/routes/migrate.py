# /app/routes/migrate.py
from flask import Blueprint, jsonify, current_app
from flask_migrate import upgrade, init, migrate, current, revision
from app import db

migrate_bp = Blueprint("migrate", __name__)

# Define routes for database migration management
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

@migrate_bp.route('/reset', methods=['POST'])
def reset_database():
    """
    Clear all data and recreate tables
    POST /api/migrate/reset
    """
    try:
        # Drop all tables
        db.drop_all()
        
        # Create all tables
        db.create_all()
        
        return jsonify({
            'message': 'Database reset successfully - all data cleared and tables recreated',
            'status': 'success'
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Database reset failed: {e}")
        return jsonify({
            'error': 'Database reset failed',
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
        from app.models.user import User
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

@migrate_bp.route('/add-s3-fields', methods=['POST'])
def add_s3_photo_fields():
    """
    Add S3 photo fields to existing tables
    POST /api/migrate/add-s3-fields
    """
    try:
        # Add profile photo fields to users table
        with db.engine.connect() as connection:
            connection.execute(db.text("""
                ALTER TABLE users 
                ADD COLUMN profile_photo_url VARCHAR(500) NULL,
                ADD COLUMN profile_photo_filename VARCHAR(255) NULL
            """))
            connection.commit()
        
        # Add S3 fields to photos table
        with db.engine.connect() as connection:
            connection.execute(db.text("""
                ALTER TABLE photos 
                ADD COLUMN s3_key VARCHAR(500) NULL,
                ADD COLUMN content_type VARCHAR(100) NULL
            """))
            connection.commit()
        
        return jsonify({
            'message': 'S3 photo fields added successfully',
            'status': 'success'
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Failed to add S3 fields: {e}")
        return jsonify({
            'error': 'Failed to add S3 fields',
            'message': str(e)
        }), 500
