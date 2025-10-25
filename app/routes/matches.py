# /app/routes/matches.py
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from datetime import datetime

from app import db, limiter
from app.models.dog import Dog
from app.models.match import Match
from app.models.user import User
from app.schemas.match_schemas import (
    SwipeActionSchema, MatchListSchema, MatchResponseSchema
)

matches_bp = Blueprint("matches", __name__)

@matches_bp.route("/swipe", methods=["POST"])
@jwt_required()
@limiter.limit("100 per minute")
def swipe_on_dog():
    try:
        current_user_id = int(get_jwt_identity())
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({"Error":"Could not validate user"}), 404
        
        schema = SwipeActionSchema()
        data = schema.load(request.json)
        
        target_dog_id = data["target_dog_id"]
        action = data["action"]
        
        target_dog = Dog.query.get(target_dog_id)
        if not target_dog:
            return jsonify({'error': 'Target dog not found'}), 404
        
        user_dog = Dog.query.filter(Dog.owner_id == current_user_id).first()
        if not user_dog:
            return jsonify({'error': 'You must have a dog profile to swipe'}), 400
        
        if not user_dog.can_be_matched_with(target_dog):
            return jsonify({'error': 'These dogs cannot be matched'}), 400
        
        # Check if match already exists
        existing_match = Match.find_existing_match(user_dog.id, target_dog_id)
        
        if existing_match:
            # Update existing match
            if existing_match.get_dog_action(user_dog.id) != 'pending':
                return jsonify({'error': 'You have already swiped on this dog'}), 400
            
            existing_match.update_action(user_dog.id, action)
            match = existing_match
        else:
            # Create new match
            match = Match.create_or_update_match(
                dog_one_id=user_dog.id,
                dog_two_id=target_dog_id,
                initiated_by_dog_id=user_dog.id,
                action=action
            )
            current_app.logger.info(f"Created match {match.id}: dog_one={match.dog_one_id} (action={match.dog_one_action}), dog_two={match.dog_two_id} (action={match.dog_two_action}), initiated_by={match.initiated_by_dog_id}")
        
        # Increment like count if it's a like or super_like
        if action in ['like', 'super_like']:
            target_dog.increment_like_count()
        
        # Prepare response
        response_data = {
            'message': f'Successfully {action}d on {target_dog.name}',
            'match': match.to_dict(current_user_id=current_user_id, include_dogs=True),
            'is_mutual_match': match.is_mutual_match()
        }
        
        # Add special message for mutual matches
        if match.is_mutual_match():
            response_data['message'] = f"It's a match! You and {target_dog.owner.get_full_name()} can now chat!"
        
        return jsonify(response_data), 200
        
    except ValidationError as e:
        return jsonify({
            'error': 'Validation failed',
            'messages': e.messages
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'Failed to process swipe',
            'message': str(e)
        }), 500

@matches_bp.route('/', methods=['GET'])
@jwt_required()
def get_matches():
    """
    Get user's matches with optional filters
    GET /api/matches?status=matched&limit=20
    """
    try:
        current_user_id = int(get_jwt_identity())
        
        # Validate query parameters
        schema = MatchListSchema()
        filters = schema.load(request.args)
        
        # Get user's dog IDs
        user_dog_ids = [dog.id for dog in Dog.query.filter(Dog.owner_id == current_user_id).all()]
        
        if not user_dog_ids:
            return jsonify({
                'matches': [],
                'count': 0,
                'message': 'You need to create a dog profile first'
            }), 200
        
        # Build query for matches involving user's dogs
        query = Match.query.filter(
            db.or_(
                Match.dog_one_id.in_(user_dog_ids),
                Match.dog_two_id.in_(user_dog_ids)
            )
        )
        
        # Apply filters
        if filters.get('status'):
            query = query.filter(Match.status == filters['status'])
        
        if not filters.get('include_archived', False):
            query = query.filter(Match.is_archived == False)
        
        # Order by most recent activity
        query = query.order_by(Match.updated_at.desc())
        
        # Apply pagination
        limit = filters.get('limit', 20)
        offset = filters.get('offset', 0)
        matches = query.limit(limit).offset(offset).all()
        
        # Convert to dict with user perspective
        matches_data = [
            match.to_dict(current_user_id=current_user_id, include_dogs=True) 
            for match in matches
        ]
        
        return jsonify({
            'matches': matches_data,
            'count': len(matches_data),
            'limit': limit,
            'offset': offset
        }), 200
        
    except ValidationError as e:
        return jsonify({
            'error': 'Validation failed',
            'messages': e.messages
        }), 400
    except Exception as e:
        return jsonify({
            'error': 'Failed to get matches',
            'message': str(e)
        }), 500


@matches_bp.route('/<int:match_id>', methods=['GET'])
@jwt_required()
def get_match(match_id):
    """
    Get specific match details
    GET /api/matches/123
    """
    try:
        current_user_id = int(get_jwt_identity())
        match = Match.query.get(match_id)
        
        if not match:
            return jsonify({'error': 'Match not found'}), 404
        
        # Check if user is part of this match
        user_dog_ids = [dog.id for dog in Dog.query.filter(Dog.owner_id == current_user_id).all()]
        
        if match.dog_one_id not in user_dog_ids and match.dog_two_id not in user_dog_ids:
            return jsonify({'error': 'You are not part of this match'}), 403
        
        # Return match details
        return jsonify({
            'match': match.to_dict(
                current_user_id=current_user_id, 
                include_dogs=True, 
                include_messages=True
            )
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to get match',
            'message': str(e)
        }), 500


@matches_bp.route('/<int:match_id>/unmatch', methods=['DELETE'])
@jwt_required()
def unmatch(match_id):
    """
    Unmatch (archive the match)
    DELETE /api/matches/123/unmatch
    """
    try:
        current_user_id = int(get_jwt_identity())
        match = Match.query.get(match_id)
        
        if not match:
            return jsonify({'error': 'Match not found'}), 404
        
        # Check if user is part of this match
        user_dog_ids = [dog.id for dog in Dog.query.filter(Dog.owner_id == current_user_id).all()]
        
        if match.dog_one_id not in user_dog_ids and match.dog_two_id not in user_dog_ids:
            return jsonify({'error': 'You are not part of this match'}), 403
        
        # Archive the match
        match.archive_match(current_user_id)
        
        return jsonify({
            'message': 'Successfully unmatched'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'Failed to unmatch',
            'message': str(e)
        }), 500


@matches_bp.route('/pending', methods=['GET'])
@jwt_required()
def get_pending_matches():
    """
    Get matches where the user hasn't swiped yet
    GET /api/matches/pending
    """
    try:
        current_user_id = int(get_jwt_identity())
        
        # Get user's dog IDs
        user_dog_ids = [dog.id for dog in Dog.query.filter(Dog.owner_id == current_user_id).all()]
        
        current_app.logger.debug(f"Pending swipes for user {current_user_id}, dog IDs: {user_dog_ids}")
        
        if not user_dog_ids:
            return jsonify({
                'pending_matches': [],
                'count': 0
            }), 200
        
        # Find matches where user's dog has pending action
        pending_matches = []
        
        for user_dog_id in user_dog_ids:
            # Matches where user's dog is dog_one and action is pending
            matches_as_dog_one = Match.query.filter(
                Match.dog_one_id == user_dog_id,
                Match.dog_one_action == 'pending'
            ).all()
            
            current_app.logger.debug(f"Dog {user_dog_id} as dog_one: {len(matches_as_dog_one)} pending matches")
            for m in matches_as_dog_one:
                current_app.logger.debug(f"Match {m.id}: dog_one={m.dog_one_id} (action={m.dog_one_action}), dog_two={m.dog_two_id} (action={m.dog_two_action})")
            
            # Matches where user's dog is dog_two and action is pending
            matches_as_dog_two = Match.query.filter(
                Match.dog_two_id == user_dog_id,
                Match.dog_two_action == 'pending'
            ).all()
            
            current_app.logger.debug(f"Dog {user_dog_id} as dog_two: {len(matches_as_dog_two)} pending matches")
            for m in matches_as_dog_two:
                current_app.logger.debug(f"Match {m.id}: dog_one={m.dog_one_id} (action={m.dog_one_action}), dog_two={m.dog_two_id} (action={m.dog_two_action})")
            
            pending_matches.extend(matches_as_dog_one)
            pending_matches.extend(matches_as_dog_two)
        
        # Convert to dict
        pending_data = [
            match.to_dict(current_user_id=current_user_id, include_dogs=True)
            for match in pending_matches
        ]
        
        return jsonify({
            'pending_matches': pending_data,
            'count': len(pending_data)
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to get pending matches',
            'message': str(e)
        }), 500


@matches_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_match_stats():
    """
    Get user's matching statistics
    GET /api/matches/stats
    """
    try:
        current_user_id = int(get_jwt_identity())
        
        # Get user's dog IDs
        user_dog_ids = [dog.id for dog in Dog.query.filter(Dog.owner_id == current_user_id).all()]
        
        if not user_dog_ids:
            return jsonify({
                'stats': {
                    'total_swipes': 0,
                    'mutual_matches': 0,
                    'pending_matches': 0,
                    'likes_given': 0,
                    'likes_received': 0
                }
            }), 200
        
        # Calculate statistics
        all_matches = Match.query.filter(
            db.or_(
                Match.dog_one_id.in_(user_dog_ids),
                Match.dog_two_id.in_(user_dog_ids)
            )
        ).all()
        
        total_swipes = len(all_matches)
        mutual_matches = len([m for m in all_matches if m.status == 'matched'])
        pending_matches = len([m for m in all_matches if m.status == 'pending'])
        
        # Count likes given and received
        likes_given = 0
        likes_received = 0
        
        for match in all_matches:
            for user_dog_id in user_dog_ids:
                if match.dog_one_id == user_dog_id:
                    if match.dog_one_action in ['like', 'super_like']:
                        likes_given += 1
                    if match.dog_two_action in ['like', 'super_like']:
                        likes_received += 1
                elif match.dog_two_id == user_dog_id:
                    if match.dog_two_action in ['like', 'super_like']:
                        likes_given += 1
                    if match.dog_one_action in ['like', 'super_like']:
                        likes_received += 1
        
        return jsonify({
            'stats': {
                'total_swipes': total_swipes,
                'mutual_matches': mutual_matches,
                'pending_matches': pending_matches,
                'likes_given': likes_given,
                'likes_received': likes_received,
                'match_rate': round((mutual_matches / max(total_swipes, 1)) * 100, 1)
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to get match stats',
            'message': str(e)
        }), 500


@matches_bp.route('/<int:match_id>/respond', methods=['POST'])
@jwt_required()
def respond_to_swipe(match_id):
    """
    Respond to a pending swipe (accept/reject)
    POST /api/matches/123/respond
    """
    try:
        current_user_id = int(get_jwt_identity())
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({"error": "Could not validate user"}), 404
        
        # Get and validate match
        match = Match.query.get(match_id)
        if not match:
            return jsonify({'error': 'Match not found'}), 404
        
        # Check if user is part of this match
        user_dog_ids = [dog.id for dog in Dog.query.filter(Dog.owner_id == current_user_id).all()]
        if match.dog_one_id not in user_dog_ids and match.dog_two_id not in user_dog_ids:
            return jsonify({'error': 'You are not part of this match'}), 403
        
        # Validate input data
        data = request.json
        if not data or 'action' not in data:
            return jsonify({'error': 'Action is required'}), 400
        
        action = data['action']
        if action not in ['like', 'pass', 'super_like']:
            return jsonify({'error': 'Invalid action. Must be like, pass, or super_like'}), 400
        
        # Check if user's dog has already responded
        user_dog_id = None
        for dog_id in user_dog_ids:
            if dog_id == match.dog_one_id:
                user_dog_id = match.dog_one_id
                current_action = match.dog_one_action
                break
            elif dog_id == match.dog_two_id:
                user_dog_id = match.dog_two_id
                current_action = match.dog_two_action
                break
        
        if not user_dog_id:
            return jsonify({'error': 'You are not part of this match'}), 403
        
        if current_action != 'pending':
            return jsonify({'error': 'You have already responded to this swipe'}), 400
        
        # Update the user's dog's action
        match.update_action(user_dog_id, action)
        
        # Prepare response
        response_data = {
            'message': f'Successfully {action}d the swipe',
            'match': match.to_dict(current_user_id=current_user_id, include_dogs=True),
            'is_mutual_match': match.is_mutual_match()
        }
        
        # Add special message for mutual matches
        if match.is_mutual_match():
            other_dog = match.get_other_dog(user_dog_id)
            response_data['message'] = f"It's a match! You and {other_dog.owner.get_full_name()} can now chat!"
        
        return jsonify(response_data), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'Failed to respond to swipe',
            'message': str(e)
        }), 500