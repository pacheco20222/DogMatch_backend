# /app/routes/users.py
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from datetime import datetime

from app import db
from app.models.user import User
from app.models.dog import Dog
from app.models.match import Match
from app.models.message import Message
from app.utils.sanitizer import sanitize_user_input
from app.schemas.user_schemas import (
    UserUpdateSchema, UserResponseSchema
)

# Create Blueprint
users_bp = Blueprint('users', __name__)

@users_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """
    Get current user's complete profile
    GET /api/users/profile
    """
    try:
        current_user_id = int(get_jwt_identity())
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get user stats
        user_dogs = Dog.query.filter(Dog.owner_id == current_user_id).all()
        
        # Get match statistics
        user_dog_ids = [dog.id for dog in user_dogs]
        total_matches = 0
        mutual_matches = 0
        
        if user_dog_ids:
            all_matches = Match.query.filter(
                db.or_(
                    Match.dog_one_id.in_(user_dog_ids),
                    Match.dog_two_id.in_(user_dog_ids)
                )
            ).all()
            
            total_matches = len(all_matches)
            mutual_matches = len([m for m in all_matches if m.status == 'matched'])
        
        # Get message statistics
        total_messages_sent = Message.query.filter(Message.sender_user_id == current_user_id).count()
        
        profile_data = user.to_dict(include_sensitive=True, include_2fa_status=True)
        profile_data.update({
            'stats': {
                'dogs_count': len(user_dogs),
                'total_matches': total_matches,
                'mutual_matches': mutual_matches,
                'messages_sent': total_messages_sent,
                'member_since': user.created_at.strftime('%B %Y') if user.created_at else None
            },
            'dogs': [dog.to_dict(include_owner=False, include_photos=True) for dog in user_dogs]
        })
        
        return jsonify({
            'profile': profile_data
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to get profile',
            'message': str(e)
        }), 500


@users_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """
    Update user profile
    PUT /api/users/profile
    """
    try:
        current_user_id = int(get_jwt_identity())
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Validate input data
        schema = UserUpdateSchema(context={'user_id': current_user_id})
        data = schema.load(request.json)
        
        current_app.logger.info(f"📸 Received profile update data: {data}")
        
        # Sanitize text fields to prevent XSS attacks
        data = sanitize_user_input(data)
        
        current_app.logger.info(f"📸 After sanitization: {data}")
        
        # Update fields
        for field, value in data.items():
            if hasattr(user, field):
                setattr(user, field, value)
                current_app.logger.info(f"📸 Setting {field} = {value}")
        
        # Update timestamp
        user.updated_at = datetime.utcnow()
        
        current_app.logger.info(f"📸 Before commit - user.profile_photo_url: {user.profile_photo_url}")
        
        # Mark as dirty and flush to ensure changes are tracked
        db.session.add(user)
        db.session.flush()
        
        # Save changes
        db.session.commit()
        
        # Refresh the user object to ensure we have the latest data
        db.session.refresh(user)
        
        current_app.logger.info(f"📸 After commit - user.profile_photo_url: {user.profile_photo_url}")
        
        user_dict = user.to_dict(include_sensitive=True)
        current_app.logger.info(f"📸 Returning user dict with profile_photo_url: {user_dict.get('profile_photo_url')}")
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': user_dict
        }), 200
        
    except ValidationError as e:
        return jsonify({
            'error': 'Validation failed',
            'messages': e.messages
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'Failed to update profile',
            'message': str(e)
        }), 500


@users_bp.route('/change-password', methods=['PUT'])
@jwt_required()
def change_password():
    """
    Change user password
    PUT /api/users/change-password
    """
    try:
        current_user_id = int(get_jwt_identity())
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.json
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        if not current_password or not new_password:
            return jsonify({'error': 'Current password and new password are required'}), 400
        
        # Verify current password
        if not user.check_password(current_password):
            return jsonify({'error': 'Current password is incorrect'}), 400
        
        # Validate new password strength
        if len(new_password) < 8:
            return jsonify({'error': 'New password must be at least 8 characters long'}), 400
        
        # Update password
        user.set_password(new_password)
        user.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Password changed successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'Failed to change password',
            'message': str(e)
        }), 500


@users_bp.route('/deactivate', methods=['PUT'])
@jwt_required()
def deactivate_account():
    """
    Deactivate user account (soft delete)
    PUT /api/users/deactivate
    """
    try:
        current_user_id = int(get_jwt_identity())
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Deactivate account
        user.is_active = False
        user.updated_at = datetime.utcnow()
        
        # Hide all user's dogs from discovery
        Dog.query.filter(Dog.owner_id == current_user_id).update({'is_available': False})
        
        db.session.commit()
        
        return jsonify({
            'message': 'Account deactivated successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'Failed to deactivate account',
            'message': str(e)
        }), 500


@users_bp.route('/reactivate', methods=['PUT'])
@jwt_required()
def reactivate_account():
    """
    Reactivate user account
    PUT /api/users/reactivate
    """
    try:
        current_user_id = int(get_jwt_identity())
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Reactivate account
        user.is_active = True
        user.updated_at = datetime.utcnow()
        
        # Make user's dogs available again
        Dog.query.filter(Dog.owner_id == current_user_id).update({'is_available': True})
        
        db.session.commit()
        
        return jsonify({
            'message': 'Account reactivated successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'Failed to reactivate account',
            'message': str(e)
        }), 500


# Admin-only endpoints
@users_bp.route('/', methods=['GET'])
@jwt_required()
def get_all_users():
    """
    Get all users (admin only)
    GET /api/users?limit=50&offset=0&user_type=owner
    """
    try:
        current_user_id = int(get_jwt_identity())
        current_user = User.query.get(current_user_id)
        
        if not current_user or not current_user.is_admin():
            return jsonify({'error': 'Admin privileges required'}), 403
        
        # Get query parameters
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        user_type = request.args.get('user_type')
        is_active = request.args.get('is_active')
        city = request.args.get('city')
        
        # Build query
        query = User.query
        
        # Apply filters
        if user_type:
            query = query.filter(User.user_type == user_type)
        if is_active is not None:
            query = query.filter(User.is_active == (is_active.lower() == 'true'))
        if city:
            query = query.filter(User.city.ilike(f'%{city}%'))
        
        # Get results with pagination
        users = query.order_by(User.created_at.desc()).limit(limit).offset(offset).all()
        
        # Convert to dict (admin can see sensitive info)
        users_data = [user.to_dict(include_sensitive=True) for user in users]
        
        return jsonify({
            'users': users_data,
            'count': len(users_data),
            'limit': limit,
            'offset': offset
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to get users',
            'message': str(e)
        }), 500


@users_bp.route('/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    """
    Get specific user (admin only or own profile)
    GET /api/users/123
    """
    try:
        current_user_id = int(get_jwt_identity())
        current_user = User.query.get(current_user_id)
        
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        # Check if user can access this profile
        if current_user_id != user_id and not current_user.is_admin():
            return jsonify({'error': 'You can only view your own profile'}), 403
        
        target_user = User.query.get(user_id)
        if not target_user:
            return jsonify({'error': 'User not found'}), 404
        
        # Include sensitive info only for admin or own profile
        include_sensitive = current_user.is_admin() or current_user_id == user_id
        
        return jsonify({
            'user': target_user.to_dict(include_sensitive=include_sensitive, include_2fa_status=True)
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to get user',
            'message': str(e)
        }), 500


@users_bp.route('/<int:user_id>/ban', methods=['PUT'])
@jwt_required()
def ban_user(user_id):
    """
    Ban/suspend user (admin only)
    PUT /api/users/123/ban
    """
    try:
        current_user_id = int(get_jwt_identity())
        current_user = User.query.get(current_user_id)
        
        if not current_user or not current_user.is_admin():
            return jsonify({'error': 'Admin privileges required'}), 403
        
        target_user = User.query.get(user_id)
        if not target_user:
            return jsonify({'error': 'User not found'}), 404
        
        if target_user.is_admin():
            return jsonify({'error': 'Cannot ban admin users'}), 400
        
        # Ban user
        target_user.is_active = False
        target_user.updated_at = datetime.utcnow()
        
        # Hide all their dogs
        Dog.query.filter(Dog.owner_id == user_id).update({'is_available': False})
        
        db.session.commit()
        
        return jsonify({
            'message': f'User {target_user.username} has been banned'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'Failed to ban user',
            'message': str(e)
        }), 500


@users_bp.route('/<int:user_id>/unban', methods=['PUT'])
@jwt_required()
def unban_user(user_id):
    """
    Unban/reactivate user (admin only)
    PUT /api/users/123/unban
    """
    try:
        current_user_id = int(get_jwt_identity())
        current_user = User.query.get(current_user_id)
        
        if not current_user or not current_user.is_admin():
            return jsonify({'error': 'Admin privileges required'}), 403
        
        target_user = User.query.get(user_id)
        if not target_user:
            return jsonify({'error': 'User not found'}), 404
        
        # Unban user
        target_user.is_active = True
        target_user.updated_at = datetime.utcnow()
        
        # Make their dogs available again
        Dog.query.filter(Dog.owner_id == user_id).update({'is_available': True})
        
        db.session.commit()
        
        return jsonify({
            'message': f'User {target_user.username} has been unbanned'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'Failed to unban user',
            'message': str(e)
        }), 500


@users_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_platform_stats():
    """
    Get platform statistics (admin only)
    GET /api/users/stats
    """
    try:
        current_user_id = int(get_jwt_identity())
        current_user = User.query.get(current_user_id)
        
        if not current_user or not current_user.is_admin():
            return jsonify({'error': 'Admin privileges required'}), 403
        
        # Calculate platform statistics
        total_users = User.query.count()
        active_users = User.query.filter(User.is_active == True).count()
        total_dogs = Dog.query.count()
        available_dogs = Dog.query.filter(Dog.is_available == True).count()
        total_matches = Match.query.count()
        mutual_matches = Match.query.filter(Match.status == 'matched').count()
        total_messages = Message.query.count()
        
        # User type breakdown
        owners = User.query.filter(User.user_type == 'owner').count()
        shelters = User.query.filter(User.user_type == 'shelter').count()
        admins = User.query.filter(User.user_type == 'admin').count()
        
        # Recent activity (last 30 days)
        from datetime import timedelta
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        new_users_30d = User.query.filter(User.created_at >= thirty_days_ago).count()
        new_dogs_30d = Dog.query.filter(Dog.created_at >= thirty_days_ago).count()
        new_matches_30d = Match.query.filter(Match.created_at >= thirty_days_ago).count()
        
        stats = {
            'users': {
                'total': total_users,
                'active': active_users,
                'inactive': total_users - active_users,
                'new_last_30_days': new_users_30d,
                'by_type': {
                    'owners': owners,
                    'shelters': shelters,
                    'admins': admins
                }
            },
            'dogs': {
                'total': total_dogs,
                'available': available_dogs,
                'unavailable': total_dogs - available_dogs,
                'new_last_30_days': new_dogs_30d
            },
            'matches': {
                'total': total_matches,
                'mutual': mutual_matches,
                'pending': total_matches - mutual_matches,
                'success_rate': round((mutual_matches / max(total_matches, 1)) * 100, 1),
                'new_last_30_days': new_matches_30d
            },
            'messages': {
                'total': total_messages
            }
        }
        
        return jsonify({
            'stats': stats,
            'generated_at': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to get platform stats',
            'message': str(e)
        }), 500
