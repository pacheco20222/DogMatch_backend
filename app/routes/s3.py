# app/routes/s3.py
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.s3_service import s3_service
from app import db
from app.models.user import User
from app.models.dog import Dog, Photo
from app.models.event import Event

s3_bp = Blueprint("s3", __name__)

@s3_bp.route('/test-connection', methods=['GET'])
@jwt_required()
def test_s3_connection():
    """
    Test S3 connection and bucket access
    GET /api/s3/test-connection
    """
    try:
        result = s3_service.test_connection()
        
        if result['success']:
            return jsonify({
                'message': 'S3 connection successful',
                'bucket': 'dogmatch-bucket',
                'status': 'success'
            }), 200
        else:
            return jsonify({
                'error': 'S3 connection failed',
                'message': result['error']
            }), 500
            
    except Exception as e:
        current_app.logger.error(f"S3 test connection error: {e}")
        return jsonify({
            'error': 'S3 test failed',
            'message': str(e)
        }), 500

@s3_bp.route('/upload/user-profile', methods=['POST'])
@jwt_required()
def upload_user_profile_photo():
    """
    Upload user profile photo to S3
    POST /api/s3/upload/user-profile
    """
    try:
        current_user_id = int(get_jwt_identity())
        
        # Check if file is provided
        if 'photo' not in request.files:
            return jsonify({'error': 'No photo file provided'}), 400
        
        file = request.files['photo']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Read file data
        file_data = file.read()
        
        # Upload to S3
        result = s3_service.upload_photo(
            file_data=file_data,
            file_type='user_profile',
            user_id=current_user_id
        )
        
        if not result['success']:
            return jsonify({'error': result['error']}), 500
        
        # Update user profile photo in database
        user = User.query.get(current_user_id)
        if user:
            user.profile_photo_url = result['url']
            user.profile_photo_filename = result['filename']
            db.session.commit()
            
            return jsonify({
                'message': 'Profile photo uploaded successfully',
                'photo_url': result['url'],
                'filename': result['filename']
            }), 200
        else:
            return jsonify({'error': 'User not found'}), 404
            
    except Exception as e:
        current_app.logger.error(f"User profile photo upload error: {e}")
        return jsonify({
            'error': 'Upload failed',
            'message': str(e)
        }), 500

@s3_bp.route('/upload/user-profile-public', methods=['POST'])
def upload_user_profile_photo_public():
    """
    Upload user profile photo to S3 during registration (no auth required)
    POST /api/s3/upload/user-profile-public
    Returns the S3 key (not full URL) to be stored in the database
    """
    try:
        # Check if file is provided
        if 'photo' not in request.files:
            return jsonify({'error': 'No photo file provided'}), 400
        
        file = request.files['photo']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Read file data
        file_data = file.read()
        
        # Upload to S3 with a temporary user_id (will use timestamp-based key)
        import time
        temp_user_id = int(time.time() * 1000)  # Use timestamp as temporary ID
        
        result = s3_service.upload_photo(
            file_data=file_data,
            file_type='user_profile',
            user_id=temp_user_id
        )
        
        if not result['success']:
            return jsonify({'error': result['error']}), 500
        
        # Return the S3 key (not full URL) so it can be stored in the database
        # The backend will generate signed URLs when needed
        return jsonify({
            'message': 'Profile photo uploaded successfully',
            'photo_url': result['url']  # This is the S3 key
        }), 200
            
    except Exception as e:
        current_app.logger.error(f"Public profile photo upload error: {e}")
        return jsonify({
            'error': 'Upload failed',
            'message': str(e)
        }), 500

@s3_bp.route('/upload/dog-photo', methods=['POST'])
@jwt_required()
def upload_dog_photo():
    """
    Upload dog photo to S3
    POST /api/s3/upload/dog-photo
    """
    try:
        current_user_id = int(get_jwt_identity())
        
        # Get dog_id from form data
        dog_id = request.form.get('dog_id')
        if not dog_id:
            return jsonify({'error': 'Dog ID is required'}), 400
        
        # Verify user owns the dog
        dog = Dog.query.filter_by(id=dog_id, owner_id=current_user_id).first()
        if not dog:
            return jsonify({'error': 'Dog not found or access denied'}), 404
        
        # Check if file is provided
        if 'photo' not in request.files:
            return jsonify({'error': 'No photo file provided'}), 400
        
        file = request.files['photo']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Read file data
        file_data = file.read()
        
        # Upload to S3
        result = s3_service.upload_photo(
            file_data=file_data,
            file_type='dog_photo',
            user_id=current_user_id,
            dog_id=dog_id
        )
        
        if not result['success']:
            return jsonify({'error': result['error']}), 500
        
        # Create photo record in database
        photo = Photo(
            dog_id=dog_id,
            url=result['url'],
            filename=result['filename'],
            s3_key=result['key'],
            content_type=result['content_type'],
            is_primary=len(dog.photos) == 0  # First photo is primary
        )
        
        db.session.add(photo)
        db.session.commit()
        
        return jsonify({
            'message': 'Dog photo uploaded successfully',
            'photo': photo.to_dict()
        }), 201
        
    except Exception as e:
        current_app.logger.error(f"Dog photo upload error: {e}")
        return jsonify({
            'error': 'Upload failed',
            'message': str(e)
        }), 500

@s3_bp.route('/upload/event-photo/<int:event_id>', methods=['POST'])
@jwt_required()
def upload_event_photo(event_id):
    """
    Upload event banner photo to S3
    POST /api/s3/upload/event-photo/<event_id>
    """
    try:
        current_user_id = int(get_jwt_identity())
        
        # Check if event exists and user has permission
        from app.models.event import Event
        event = Event.query.get(event_id)
        if not event:
            return jsonify({'error': 'Event not found'}), 404
        
        # Check if user is the organizer or admin
        from app.models.user import User
        user = User.query.get(current_user_id)
        if event.organizer_id != current_user_id and not user.is_admin():
            return jsonify({'error': 'Access denied. Only event organizers can upload photos.'}), 403
        
        # Check if file is provided
        if 'photo' not in request.files:
            return jsonify({'error': 'No photo file provided'}), 400
        
        file = request.files['photo']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Read file data
        file_data = file.read()
        
        # Upload to S3
        result = s3_service.upload_photo(
            file_data=file_data,
            file_type='event_photo',
            user_id=current_user_id,
            event_id=event_id
        )
        
        if not result['success']:
            return jsonify({'error': result['error']}), 500
        
        # Update event image in database
        event.image_url = result['url']
        event.image_filename = result['filename']
        db.session.commit()
        
        return jsonify({
            'message': 'Event photo uploaded successfully',
            'photo_url': result['url'],
            'filename': result['filename']
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Event photo upload error: {e}")
        return jsonify({
            'error': 'Upload failed',
            'message': str(e)
        }), 500

@s3_bp.route('/delete/photo/<int:photo_id>', methods=['DELETE'])
@jwt_required()
def delete_photo(photo_id):
    """
    Delete a photo from S3 and database
    DELETE /api/s3/delete/photo/<photo_id>
    """
    try:
        current_user_id = int(get_jwt_identity())
        
        # Find the photo
        photo = Photo.query.get(photo_id)
        if not photo:
            return jsonify({'error': 'Photo not found'}), 404
        
        # Verify user owns the dog
        if photo.dog.owner_id != current_user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        # Delete from S3 if it's an S3 photo
        if photo.is_s3_photo() and photo.s3_key:
            delete_result = s3_service.delete_photo(photo.s3_key)
            if not delete_result['success']:
                current_app.logger.warning(f"Failed to delete S3 photo: {delete_result['error']}")
        
        # Delete from database
        db.session.delete(photo)
        db.session.commit()
        
        return jsonify({
            'message': 'Photo deleted successfully'
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Photo deletion error: {e}")
        return jsonify({
            'error': 'Deletion failed',
            'message': str(e)
        }), 500
