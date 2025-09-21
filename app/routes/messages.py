# /app/routes/messages.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from datetime import datetime

from app import db
from app.models import (
    Message, Match, User,
    MessageCreateSchema, MessageUpdateSchema, MessageResponseSchema, MessageListSchema
)

# Create Blueprint
messages_bp = Blueprint('messages', __name__)

@messages_bp.route('/matches/<int:match_id>/messages', methods=['POST'])
@jwt_required()
def send_message(match_id):
    """
    Send a message in a match conversation
    POST /api/messages/matches/123/messages
    """
    try:
        current_user_id = int(get_jwt_identity())
        
        # Get and validate match
        match = Match.query.get(match_id)
        if not match:
            return jsonify({'error': 'Match not found'}), 404
        
        # Check if user is part of this match
        user_dog_ids = [dog.id for dog in User.query.get(current_user_id).dogs]
        if match.dog_one_id not in user_dog_ids and match.dog_two_id not in user_dog_ids:
            return jsonify({'error': 'You are not part of this match'}), 403
        
        # Check if users can send messages (must be mutual match)
        if not match.can_send_messages():
            return jsonify({'error': 'Cannot send messages to this match'}), 403
        
        # Validate input data
        schema = MessageCreateSchema()
        data = schema.load(request.json)
        
        # Create message
        message = Message(
            match_id=match_id,
            sender_user_id=current_user_id,
            content=data['content'],
            message_type=data.get('message_type', 'text'),
            image_url=data.get('image_url'),
            image_filename=data.get('image_filename'),
            latitude=data.get('latitude'),
            longitude=data.get('longitude'),
            location_name=data.get('location_name')
        )
        
        # Save to database
        db.session.add(message)
        db.session.commit()
        
        # Update match message stats
        match.update_message_stats()
        
        return jsonify({
            'message': 'Message sent successfully',
            'data': message.to_dict(current_user_id=current_user_id)
        }), 201
        
    except ValidationError as e:
        return jsonify({
            'error': 'Validation failed',
            'messages': e.messages
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'Failed to send message',
            'message': str(e)
        }), 500


@messages_bp.route('/matches/<int:match_id>/messages', methods=['GET'])
@jwt_required()
def get_messages(match_id):
    """
    Get messages for a match conversation
    GET /api/messages/matches/123/messages?limit=50&offset=0
    """
    try:
        current_user_id = int(get_jwt_identity())
        
        # Validate query parameters
        schema = MessageListSchema()
        filters = schema.load(request.args)
        
        # Get and validate match
        match = Match.query.get(match_id)
        if not match:
            return jsonify({'error': 'Match not found'}), 404
        
        # Check if user is part of this match
        user_dog_ids = [dog.id for dog in User.query.get(current_user_id).dogs]
        if match.dog_one_id not in user_dog_ids and match.dog_two_id not in user_dog_ids:
            return jsonify({'error': 'You are not part of this match'}), 403
        
        # Build query
        query = Message.query.filter(Message.match_id == match_id)
        
        # Apply filters
        if not filters.get('include_deleted', False):
            query = query.filter(Message.is_deleted == False)
        
        # Apply pagination and ordering
        limit = filters.get('limit', 50)
        offset = filters.get('offset', 0)
        
        if filters.get('before_message_id'):
            query = query.filter(Message.id < filters['before_message_id'])
        
        messages = query.order_by(Message.sent_at.desc()).limit(limit).offset(offset).all()
        
        # Reverse to get chronological order (oldest first)
        messages = list(reversed(messages))
        
        # Auto-mark messages as read if requested
        if filters.get('mark_as_read', True):
            unread_messages = [msg for msg in messages 
                             if msg.sender_user_id != current_user_id and not msg.is_read]
            for msg in unread_messages:
                msg.mark_as_read()
        
        # Convert to dict
        messages_data = [msg.to_dict(current_user_id=current_user_id) for msg in messages]
        
        return jsonify({
            'messages': messages_data,
            'count': len(messages_data),
            'limit': limit,
            'offset': offset,
            'match_info': {
                'id': match.id,
                'status': match.status,
                'can_send_messages': match.can_send_messages()
            }
        }), 200
        
    except ValidationError as e:
        return jsonify({
            'error': 'Validation failed',
            'messages': e.messages
        }), 400
    except Exception as e:
        return jsonify({
            'error': 'Failed to get messages',
            'message': str(e)
        }), 500


@messages_bp.route('/<int:message_id>', methods=['PUT'])
@jwt_required()
def edit_message(message_id):
    """
    Edit a message (only text messages, within time limit)
    PUT /api/messages/123
    """
    try:
        current_user_id = int(get_jwt_identity())
        
        # Get message
        message = Message.query.get(message_id)
        if not message:
            return jsonify({'error': 'Message not found'}), 404
        
        # Check if user can edit this message
        if not message.can_be_edited_by(current_user_id):
            return jsonify({'error': 'You cannot edit this message'}), 403
        
        # Validate input data
        schema = MessageUpdateSchema()
        data = schema.load(request.json)
        
        # Update message
        message.edit_content(data['content'])
        
        return jsonify({
            'message': 'Message updated successfully',
            'data': message.to_dict(current_user_id=current_user_id)
        }), 200
        
    except ValidationError as e:
        return jsonify({
            'error': 'Validation failed',
            'messages': e.messages
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'Failed to edit message',
            'message': str(e)
        }), 500


@messages_bp.route('/<int:message_id>', methods=['DELETE'])
@jwt_required()
def delete_message(message_id):
    """
    Delete a message (soft delete)
    DELETE /api/messages/123
    """
    try:
        current_user_id = int(get_jwt_identity())
        
        # Get message
        message = Message.query.get(message_id)
        if not message:
            return jsonify({'error': 'Message not found'}), 404
        
        # Check if user can delete this message
        if not message.can_be_deleted_by(current_user_id):
            return jsonify({'error': 'You cannot delete this message'}), 403
        
        # Soft delete message
        message.soft_delete(current_user_id)
        
        return jsonify({
            'message': 'Message deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'Failed to delete message',
            'message': str(e)
        }), 500


@messages_bp.route('/<int:message_id>/read', methods=['POST'])
@jwt_required()
def mark_message_read(message_id):
    """
    Mark a specific message as read
    POST /api/messages/123/read
    """
    try:
        current_user_id = int(get_jwt_identity())
        
        # Get message
        message = Message.query.get(message_id)
        if not message:
            return jsonify({'error': 'Message not found'}), 404
        
        # Check if user is the recipient (not the sender)
        if message.sender_user_id == current_user_id:
            return jsonify({'error': 'You cannot mark your own message as read'}), 400
        
        # Check if user is part of the match
        user_dog_ids = [dog.id for dog in User.query.get(current_user_id).dogs]
        if (message.match.dog_one_id not in user_dog_ids and 
            message.match.dog_two_id not in user_dog_ids):
            return jsonify({'error': 'You are not part of this conversation'}), 403
        
        # Mark as read
        message.mark_as_read()
        
        return jsonify({
            'message': 'Message marked as read'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'Failed to mark message as read',
            'message': str(e)
        }), 500


@messages_bp.route('/matches/<int:match_id>/messages/unread-count', methods=['GET'])
@jwt_required()
def get_unread_count(match_id):
    """
    Get count of unread messages in a match
    GET /api/messages/matches/123/messages/unread-count
    """
    try:
        current_user_id = int(get_jwt_identity())
        
        # Get and validate match
        match = Match.query.get(match_id)
        if not match:
            return jsonify({'error': 'Match not found'}), 404
        
        # Check if user is part of this match
        user_dog_ids = [dog.id for dog in User.query.get(current_user_id).dogs]
        if match.dog_one_id not in user_dog_ids and match.dog_two_id not in user_dog_ids:
            return jsonify({'error': 'You are not part of this match'}), 403
        
        # Count unread messages (not sent by current user)
        unread_count = Message.query.filter(
            Message.match_id == match_id,
            Message.sender_user_id != current_user_id,
            Message.is_read == False,
            Message.is_deleted == False
        ).count()
        
        return jsonify({
            'unread_count': unread_count,
            'match_id': match_id
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to get unread count',
            'message': str(e)
        }), 500


@messages_bp.route('/conversations', methods=['GET'])
@jwt_required()
def get_conversations():
    """
    Get all conversations (matches with messages) for the user
    GET /api/messages/conversations
    """
    try:
        current_user_id = int(get_jwt_identity())
        
        # Get user's dog IDs
        user_dog_ids = [dog.id for dog in User.query.get(current_user_id).dogs]
        
        if not user_dog_ids:
            return jsonify({
                'conversations': [],
                'count': 0
            }), 200
        
        # Get matches with messages
        matches_with_messages = Match.query.filter(
            db.or_(
                Match.dog_one_id.in_(user_dog_ids),
                Match.dog_two_id.in_(user_dog_ids)
            ),
            Match.status == 'matched',
            Match.is_active == True,
            Match.is_archived == False,
            Match.message_count > 0
        ).order_by(Match.last_message_at.desc()).all()
        
        conversations = []
        for match in matches_with_messages:
            # Get last message
            last_message = Message.query.filter(
                Message.match_id == match.id,
                Message.is_deleted == False
            ).order_by(Message.sent_at.desc()).first()
            
            # Get unread count
            unread_count = Message.query.filter(
                Message.match_id == match.id,
                Message.sender_user_id != current_user_id,
                Message.is_read == False,
                Message.is_deleted == False
            ).count()
            
            conversation_data = {
                'match': match.to_dict(current_user_id=current_user_id, include_dogs=True),
                'last_message': last_message.to_dict(current_user_id=current_user_id) if last_message else None,
                'unread_count': unread_count,
                'updated_at': match.last_message_at.isoformat() if match.last_message_at else None
            }
            
            conversations.append(conversation_data)
        
        return jsonify({
            'conversations': conversations,
            'count': len(conversations)
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to get conversations',
            'message': str(e)
        }), 500


@messages_bp.route('/system', methods=['POST'])
@jwt_required()
def create_system_message():
    """
    Create a system message (for match notifications, etc.)
    POST /api/messages/system
    """
    try:
        current_user_id = int(get_jwt_identity())
        
        # Only allow admins or the system to create system messages
        user = User.query.get(current_user_id)
        if not user or not user.is_admin():
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        data = request.json
        match_id = data.get('match_id')
        message_type = data.get('message_type', 'match_created')
        content = data.get('content', 'System message')
        system_data = data.get('system_data')
        
        if not match_id:
            return jsonify({'error': 'Match ID is required'}), 400
        
        # Create system message
        message = Message.create_system_message(
            match_id=match_id,
            message_type=message_type,
            content=content,
            system_data=system_data
        )
        
        return jsonify({
            'message': 'System message created successfully',
            'data': message.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'Failed to create system message',
            'message': str(e)
        }), 500