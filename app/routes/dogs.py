# /app/routes/dogs.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from datetime import datetime
from app import db

from app.models import(
    Dog, Photo, User,
    DogCreateSchema, DogUpdateSchema, DogResponseSchema
)

dogs_bp = Blueprint("dogs", __name__)

@dogs_bp.route("/", methods=["POST"])
@jwt_required()
def create_dog():
    try:
        current_user_id = int(get_jwt_identity())
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({"Error":"Invalid User, User has not been found"}), 404
        
        schema = DogCreateSchema()
        data = schema.load(request.json)
        
        dog = Dog(
            name=data['name'],
            gender=data['gender'],
            size=data['size'],
            owner_id=current_user_id,
            age=data.get('age'),
            age_months=data.get('age_months'),
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
            latitude=data.get('latitude'),
            longitude=data.get('longitude'),
            availability_type=data.get('availability_type', 'playdate'),
            adoption_fee=data.get('adoption_fee')
        )

        if data.get('personality'):
            dog.set_personality_list(data['personality'])
            
        db.session.add(dog)
        db.session.commit()
        
        return jsonify({
            "Message":"Dog created",
            "Dog": dog.to_dict(include_owner=True, include_photos=True)
        }), 201
        
    except ValidationError as e:
        return jsonify({
            "Error":"Validation Error",
            "Message": e.messages
        }), 400
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'Failed to create dog profile',
            'message': str(e)
        }), 500
        
@dogs_bp.route('/', methods=['GET'])
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
    Get dogs for swiping (excludes user's own dogs)
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
        
        # Build query - exclude user's own dogs
        query = Dog.query.filter(
            Dog.owner_id != current_user_id,
            Dog.is_available == True,
            Dog.is_adopted == False
        )
        
        # Apply preferences
        if size_preference:
            query = query.filter(Dog.size == size_preference)
        
        # TODO: Add distance filtering when lat/lng provided
        # TODO: Add already-swiped exclusion (requires Match model integration)
        
        # Get random selection of dogs
        dogs = query.order_by(db.func.random()).limit(limit).all()
        
        # Convert to dict
        dogs_data = [dog.to_dict(include_owner=True, include_photos=True) for dog in dogs]
        
        return jsonify({
            'dogs': dogs_data,
            'count': len(dogs_data)
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to discover dogs',
            'message': str(e)
        }), 500


@dogs_bp.route('/my-dogs', methods=['GET'])
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
    """
    try:
        current_user_id = int(get_jwt_identity())
        dog = Dog.query.get(dog_id)
        
        if not dog:
            return jsonify({'error': 'Dog not found'}), 404
        
        # Check if user owns this dog
        if dog.owner_id != current_user_id:
            return jsonify({'error': 'You can only add photos to your own dogs'}), 403
        
        # Get photo data from request
        data = request.json
        photo_url = data.get('url')
        filename = data.get('filename')
        is_primary = data.get('is_primary', False)
        
        if not photo_url:
            return jsonify({'error': 'Photo URL is required'}), 400
        
        # Create photo record
        photo = Photo(
            dog_id=dog_id,
            url=photo_url,
            filename=filename,
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
        
        # Delete photo
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