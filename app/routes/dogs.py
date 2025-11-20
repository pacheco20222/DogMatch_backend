# /app/routes/dogs.py
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from datetime import datetime
import os
import uuid
from werkzeug.utils import secure_filename
from app import db
from app.services.s3_service import S3Service
from app.models.dog import Dog, Photo
from app.models.user import User
from app.utils.sanitizer import sanitize_dog_input
from app.schemas.dog_schemas import (
    DogCreateSchema, DogUpdateSchema, DogResponseSchema
)

# Define Blueprint
dogs_bp = Blueprint("dogs", __name__)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def save_uploaded_file(file, dog_id, user_id):
    """Upload file to S3 and return the S3 URL, key, and filename"""
    if file and allowed_file(file.filename):
        # Initialize S3 service
        s3_service = S3Service()
        
        # Read file data
        file_data = file.read()
        
        # Upload to S3
        result = s3_service.upload_photo(
            file_data=file_data,
            file_type='dog_photo',
            user_id=user_id,
            dog_id=dog_id
        )
        
        if result['success']:
            current_app.logger.info(f"File uploaded to S3: {result['key']}")
            return result['filename'], result['url'], result['key']
        else:
            current_app.logger.error(f"S3 upload failed: {result.get('error')}")
            return None, None, None
    
    return None, None, None

@dogs_bp.route("/", methods=["POST"], strict_slashes=False)
@jwt_required()
def create_dog():
    try:
        current_user_id = int(get_jwt_identity())
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({"Error":"Invalid User, User has not been found"}), 404
        
        # Log incoming data for debugging
        current_app.logger.debug(f"Incoming request data: {request.json}")
        
        schema = DogCreateSchema()
        data = schema.load(request.json)
        
        # Sanitize text fields to prevent XSS attacks
        data = sanitize_dog_input(data)
        
        current_app.logger.debug(f"Validated data: {data}")
        
        dog = Dog(
            name=data['name'],
            gender=data['gender'],
            size=data['size'],
            owner_id=current_user_id,
            age_years=data.get('age_years'),
            breed=data.get('breed'),
            weight=data.get('weight'),
            color=data.get('color'),
            energy_level=data.get('energy_level'),
            good_with_kids=data.get('good_with_kids'),
            good_with_dogs=data.get('good_with_dogs'),
            good_with_cats=data.get('good_with_cats'),
            is_vaccinated=data.get('is_vaccinated', False),
            is_neutered=data.get('is_neutered'),
            health_notes=data.get('health_notes'),
            special_needs=data.get('special_needs'),
            description=data.get('description'),
            location=data.get('location'),
            availability_type=data.get('availability_type', 'playdate'),
            adoption_fee=data.get('adoption_fee')
        )

        if data.get('personality'):
            dog.set_personality_list(data['personality'])
            
        db.session.add(dog)
        db.session.commit()
        
        return jsonify({
            "message": "Dog created successfully",
            "dog": dog.to_dict(include_owner=True, include_photos=True)
        }), 201
        
    except ValidationError as e:
        current_app.logger.error(f"Validation error: {e.messages}")
        return jsonify({
            "Error":"Validation Error",
            "Message": e.messages
        }), 400
        
    except Exception as e:
        current_app.logger.error(f"Exception creating dog: {str(e)}")
        current_app.logger.debug(f"Exception type: {type(e)}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return jsonify({
            'error': 'Failed to create dog profile',
            'message': str(e)
        }), 500
        
@dogs_bp.route('/', methods=['GET'], strict_slashes=False)
def get_dogs():
    """
    Get dogs with optional filters
    GET /api/dogs?size=medium&city=Mérida&availability_type=playdate
    """
    try:
        # Get query parameters for filtering
        size = request.args.get('size')
        city = request.args.get('city')
        state = request.args.get('state')
        availability_type = request.args.get('availability_type')
        breed = request.args.get('breed')
        energy_level = request.args.get('energy_level')
        good_with_kids = request.args.get('good_with_kids')
        is_available = request.args.get('is_available', 'true').lower() == 'true'
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))
        
        # Build query
        query = Dog.query.filter(Dog.is_available == is_available)
        
        # Apply filters
        if size:
            query = query.filter(Dog.size == size)
        if city:
            query = query.filter(Dog.location.ilike(f'%{city}%'))
        if availability_type:
            query = query.filter(Dog.availability_type == availability_type)
        if breed:
            query = query.filter(Dog.breed.ilike(f'%{breed}%'))
        if energy_level:
            query = query.filter(Dog.energy_level == energy_level)
        if good_with_kids:
            query = query.filter(Dog.good_with_kids == (good_with_kids.lower() == 'true'))
        
        # Get results with pagination
        dogs = query.order_by(Dog.created_at.desc()).limit(limit).offset(offset).all()
        
        # Convert to dict
        dogs_data = [dog.to_dict(include_owner=True, include_photos=True) for dog in dogs]
        
        return jsonify({
            'dogs': dogs_data,
            'count': len(dogs_data),
            'limit': limit,
            'offset': offset
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to get dogs',
            'message': str(e)
        }), 500

@dogs_bp.route('/<int:dog_id>', methods=['GET'])
def get_dog(dog_id):
    """
    Get specific dog by ID
    GET /api/dogs/123
    """
    try:
        dog = Dog.query.get(dog_id)
        
        if not dog:
            return jsonify({'error': 'Dog not found'}), 404
        
        # Increment view count
        dog.increment_view_count()
        
        return jsonify({
            'dog': dog.to_dict(include_owner=True, include_photos=True, include_stats=True)
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to get dog',
            'message': str(e)
        }), 500


@dogs_bp.route('/<int:dog_id>', methods=['PUT'])
@jwt_required()
def update_dog(dog_id):
    """
    Update dog profile
    PUT /api/dogs/123
    """
    try:
        current_user_id = int(get_jwt_identity())
        dog = Dog.query.get(dog_id)
        
        if not dog:
            return jsonify({'error': 'Dog not found'}), 404
        
        # Check if user owns this dog
        if dog.owner_id != current_user_id:
            return jsonify({'error': 'You can only update your own dogs'}), 403
        
        # Validate input data
        schema = DogUpdateSchema()
        data = schema.load(request.json)
        
        # Sanitize text fields to prevent XSS attacks
        data = sanitize_dog_input(data)
        
        # Update fields
        for field, value in data.items():
            if field == 'personality':
                dog.set_personality_list(value)
            elif hasattr(dog, field):
                setattr(dog, field, value)
        
        # Update timestamp
        dog.updated_at = datetime.utcnow()
        
        # Save changes
        db.session.commit()
        
        return jsonify({
            'message': 'Dog profile updated successfully',
            'dog': dog.to_dict(include_owner=True, include_photos=True)
        }), 200
        
    except ValidationError as e:
        return jsonify({
            'error': 'Validation failed',
            'messages': e.messages
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'Failed to update dog profile',
            'message': str(e)
        }), 500


@dogs_bp.route('/<int:dog_id>', methods=['DELETE'])
@jwt_required()
def delete_dog(dog_id):
    """
    Delete dog profile
    DELETE /api/dogs/123
    """
    try:
        current_user_id = int(get_jwt_identity())
        dog = Dog.query.get(dog_id)
        
        if not dog:
            return jsonify({'error': 'Dog not found'}), 404
        
        # Check if user owns this dog
        if dog.owner_id != current_user_id:
            return jsonify({'error': 'You can only delete your own dogs'}), 403
        
        # Delete dog (cascade will handle related records)
        db.session.delete(dog)
        db.session.commit()
        
        return jsonify({
            'message': 'Dog profile deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'Failed to delete dog profile',
            'message': str(e)
        }), 500


@dogs_bp.route('/discover', methods=['GET'])
@jwt_required()
def discover_dogs():
    """
    Get dogs for swiping (excludes user's own dogs and already-swiped dogs)
    GET /api/dogs/discover?limit=10
    """
    try:
        current_user_id = int(get_jwt_identity())
        
        # Get query parameters
        limit = int(request.args.get('limit', 10))
        size_preference = request.args.get('size')
        max_distance = request.args.get('max_distance')  # in kilometers
        user_latitude = request.args.get('user_latitude')
        user_longitude = request.args.get('user_longitude')
        
        # Get user's dog IDs
        user_dog_ids = [dog.id for dog in Dog.query.filter(Dog.owner_id == current_user_id).all()]
        
        if not user_dog_ids:
            return jsonify({
                'dogs': [],
                'count': 0,
                'message': 'You need to create a dog profile first'
            }), 200
        
        # Get dogs that user has already swiped on (any action)
        from app.models.match import Match
        swiped_dog_ids = set()
        
        # Find all matches where user's dogs have swiped (any action)
        matches = Match.query.filter(
            db.or_(
                Match.dog_one_id.in_(user_dog_ids),
                Match.dog_two_id.in_(user_dog_ids)
            )
        ).all()
        
        for match in matches:
            # Add the other dog's ID to swiped list
            if match.dog_one_id in user_dog_ids:
                swiped_dog_ids.add(match.dog_two_id)
            else:
                swiped_dog_ids.add(match.dog_one_id)
        
        # Build query - exclude user's own dogs and already-swiped dogs
        query = Dog.query.filter(
            Dog.owner_id != current_user_id,
            Dog.is_available == True,
            Dog.is_adopted == False,
            ~Dog.id.in_(swiped_dog_ids)  # Exclude already-swiped dogs
        )
        
        # Apply preferences
        if size_preference:
            query = query.filter(Dog.size == size_preference)
        
        # TODO: Add distance filtering when lat/lng provided
        
        # Get random selection of dogs
        dogs = query.order_by(db.func.random()).limit(limit).all()
        
        # Convert to dict with owner information
        dogs_data = [dog.to_dict(include_owner=True, include_photos=True) for dog in dogs]
        
        return jsonify({
            'dogs': dogs_data,
            'count': len(dogs_data),
            'swiped_count': len(swiped_dog_ids)
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to discover dogs',
            'message': str(e)
        }), 500


@dogs_bp.route('/my-dogs', methods=['GET'], strict_slashes=False)
@jwt_required()
def get_my_dogs():
    """
    Get current user's dogs
    GET /api/dogs/my-dogs
    """
    try:
        current_user_id = int(get_jwt_identity())
        
        # Get user's dogs
        dogs = Dog.query.filter(Dog.owner_id == current_user_id).order_by(Dog.created_at.desc()).all()
        
        # Convert to dict
        dogs_data = [dog.to_dict(include_owner=False, include_photos=True, include_stats=True) for dog in dogs]
        
        return jsonify({
            'dogs': dogs_data,
            'count': len(dogs_data)
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to get your dogs',
            'message': str(e)
        }), 500


# Photo management endpoints
@dogs_bp.route('/<int:dog_id>/photos', methods=['POST'])
@jwt_required()
def add_dog_photo(dog_id):
    """
    Add photo to dog profile
    POST /api/dogs/123/photos
    Accepts both file uploads and JSON with URL
    """
    try:
        current_user_id = int(get_jwt_identity())
        dog = Dog.query.get(dog_id)
        
        if not dog:
            return jsonify({'error': 'Dog not found'}), 404
        
        # Check if user owns this dog
        if dog.owner_id != current_user_id:
            return jsonify({'error': 'You can only add photos to your own dogs'}), 403
        
        # Debug logging
        current_app.logger.debug(f"Request files: {request.files}")
        current_app.logger.debug(f"Request form: {request.form}")
        current_app.logger.debug(f"Request content type: {request.content_type}")
        current_app.logger.debug(f"Request is_json: {request.is_json}")
        
        # Handle file upload
        if 'photo' in request.files:
            file = request.files['photo']
            is_primary = request.form.get('is_primary', 'false').lower() == 'true'
            
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
            
            # Upload to S3
            filename, photo_url, s3_key = save_uploaded_file(file, dog_id, current_user_id)
            
            if not photo_url:
                return jsonify({'error': 'Invalid file type or upload failed. Allowed: png, jpg, jpeg, gif'}), 400
        
        # Handle JSON with URL (for external URLs or testing)
        elif request.is_json:
            data = request.json
            photo_url = data.get('url')
            filename = data.get('filename')
            s3_key = data.get('s3_key')
            is_primary = data.get('is_primary', False)
            
            if not photo_url:
                return jsonify({'error': 'Photo URL is required'}), 400
        
        else:
            return jsonify({'error': 'No photo provided. Send file as "photo" or JSON with "url"'}), 400
        
        # Check if this is the first photo for this dog - make it primary automatically
        existing_photos_count = Photo.query.filter_by(dog_id=dog_id).count()
        if existing_photos_count == 0:
            is_primary = True
        
        # Create photo record
        photo = Photo(
            dog_id=dog_id,
            url=photo_url,
            filename=filename,
            s3_key=s3_key,
            is_primary=is_primary
        )
        
        # If this is set as primary, unset others
        if is_primary:
            Photo.query.filter(Photo.dog_id == dog_id).update({'is_primary': False})
        
        db.session.add(photo)
        db.session.commit()
        
        return jsonify({
            'message': 'Photo added successfully',
            'photo': photo.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'Failed to add photo',
            'message': str(e)
        }), 500


@dogs_bp.route('/<int:dog_id>/photos/<int:photo_id>', methods=['DELETE'])
@jwt_required()
def delete_dog_photo(dog_id, photo_id):
    """
    Delete dog photo
    DELETE /api/dogs/123/photos/456
    """
    try:
        current_user_id = int(get_jwt_identity())
        dog = Dog.query.get(dog_id)
        
        if not dog:
            return jsonify({'error': 'Dog not found'}), 404
        
        # Check if user owns this dog
        if dog.owner_id != current_user_id:
            return jsonify({'error': 'You can only delete photos from your own dogs'}), 403
        
        photo = Photo.query.filter(Photo.id == photo_id, Photo.dog_id == dog_id).first()
        
        if not photo:
            return jsonify({'error': 'Photo not found'}), 404
        
        # Delete file from filesystem if it's a local file
        if photo.url.startswith('/static/dog_photos/'):
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], photo.filename)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except OSError:
                    pass  # File might already be deleted, continue
        
        # Delete photo record
        db.session.delete(photo)
        db.session.commit()
        
        return jsonify({
            'message': 'Photo deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'Failed to delete photo',
            'message': str(e)
        }), 500