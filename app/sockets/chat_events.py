# Socket.IO event handlers for real-time chat functionality
from flask import request
from flask_jwt_extended import decode_token
from flask_socketio import emit, join_room, leave_room, disconnect
from app import socketio, db
from app.models import User, Match, Message, Dog
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Store active users and their socket sessions
active_users = {}  # {user_id: [socket_ids]}
user_rooms = {}    # {socket_id: [room_names]}

def authenticate_user():
    """Authenticate user from JWT token in query params"""
    try:
        token = request.args.get('token')
        if not token:
            logger.warning("No token provided for socket connection")
            return None
        
        # Decode JWT token
        decoded_token = decode_token(token)
        user_id = decoded_token['sub']
        
        # Verify user exists
        user = User.query.get(user_id)
        if not user:
            logger.warning(f"User {user_id} not found")
            return None
            
        return user
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        return None

@socketio.on('connect')
def handle_connect():
    """Handle client connection with JWT authentication"""
    user = authenticate_user()
    if not user:
        logger.warning("Unauthorized socket connection attempt")
        disconnect()
        return False
    
    # Store user session
    if user.id not in active_users:
        active_users[user.id] = []
    active_users[user.id].append(request.sid)
    user_rooms[request.sid] = []
    
    logger.info(f"🔵 CONNECT: User {user.id} ({user.email}) connected with socket {request.sid}")
    logger.info(f"📱 ACTIVE_USERS after connect: {dict(active_users)}")
    
    # Emit connection confirmation
    emit('connected', {
        'user_id': user.id,
        'message': 'Successfully connected to chat'
    })
    
    # Notify other users that this user is online
    emit('user_online', {
        'user_id': user.id,
        'username': user.username,
        'first_name': user.first_name
    }, broadcast=True, include_self=False)

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    # Find user by socket ID
    user_id = None
    for uid, socket_ids in active_users.items():
        if request.sid in socket_ids:
            user_id = uid
            socket_ids.remove(request.sid)
            if not socket_ids:  # No more sessions for this user
                del active_users[uid]
            break
    
    if user_id:
        logger.info(f"User {user_id} disconnected (socket {request.sid})")
        
        # Clean up rooms
        if request.sid in user_rooms:
            del user_rooms[request.sid]
        
        # Notify other users that this user is offline
        emit('user_offline', {
            'user_id': user_id
        }, broadcast=True, include_self=False)

@socketio.on('join_match')
def handle_join_match(data):
    """Join a match room for real-time updates"""
    user = authenticate_user()
    if not user:
        return False
    
    match_id = data.get('match_id')
    if not match_id:
        emit('error', {'message': 'Match ID is required'})
        return
    
    # Verify user is part of this match
    match = Match.query.get(match_id)
    if not match:
        emit('error', {'message': 'Match not found'})
        return
    
    # Check if user is part of this match
    user_dog_ids = [dog.id for dog in user.dogs]
    if match.dog_one_id not in user_dog_ids and match.dog_two_id not in user_dog_ids:
        emit('error', {'message': 'You are not part of this match'})
        return
    
    # Join the room
    room_name = f"match_{match_id}"
    join_room(room_name)
    
    # Track room membership
    if request.sid not in user_rooms:
        user_rooms[request.sid] = []
    user_rooms[request.sid].append(room_name)
    
    logger.info(f"🟢 JOIN_MATCH: User {user.id} (socket {request.sid}) joined room {room_name}")
    logger.info(f"📍 USER_ROOMS after join: {dict(user_rooms)}")
    
    emit('joined_match', {
        'match_id': match_id,
        'room': room_name,
        'message': f'Joined match {match_id}'
    })

@socketio.on('leave_match')
def handle_leave_match(data):
    """Leave a match room"""
    user = authenticate_user()
    if not user:
        return False
    
    match_id = data.get('match_id')
    if not match_id:
        emit('error', {'message': 'Match ID is required'})
        return
    
    room_name = f"match_{match_id}"
    leave_room(room_name)
    
    # Remove from tracking
    if request.sid in user_rooms and room_name in user_rooms[request.sid]:
        user_rooms[request.sid].remove(room_name)
    
    logger.info(f"User {user.id} left match room {room_name}")
    
    emit('left_match', {
        'match_id': match_id,
        'room': room_name,
        'message': f'Left match {match_id}'
    })

@socketio.on('send_message')
def handle_send_message(data):
    """Handle sending a message in a match"""
    user = authenticate_user()
    if not user:
        return False
    
    match_id = data.get('match_id')
    content = data.get('content', '').strip()
    message_type = data.get('message_type', 'text')
    
    if not match_id or not content:
        emit('error', {'message': 'Match ID and content are required'})
        return
    
    # Verify match exists and user is part of it
    match = Match.query.get(match_id)
    if not match:
        emit('error', {'message': 'Match not found'})
        return
    
    # Check if user is part of this match
    user_dog_ids = [dog.id for dog in user.dogs]
    if match.dog_one_id not in user_dog_ids and match.dog_two_id not in user_dog_ids:
        emit('error', {'message': 'You are not part of this match'})
        return
    
    # Check if users can send messages (must be mutual match)
    if not match.can_send_messages():
        emit('error', {'message': 'Cannot send messages to this match'})
        return
    
    try:
        # Create message in database
        message = Message(
            match_id=match_id,
            sender_user_id=user.id,
            content=content,
            message_type=message_type,
            image_url=data.get('image_url'),
            image_filename=data.get('image_filename'),
            latitude=data.get('latitude'),
            longitude=data.get('longitude'),
            location_name=data.get('location_name')
        )
        
        db.session.add(message)
        db.session.commit()
        
        # Update match message stats
        match.update_message_stats()
        
        # Prepare message data for broadcast
        # Send to sender with is_sent_by_me=True
        sender_message_data = message.to_dict(current_user_id=user.id)
        
        # Send to other users with is_sent_by_me=False
        recipient_message_data = message.to_dict(current_user_id=None)
        recipient_message_data['is_sent_by_me'] = False
        
        # Broadcast to all users in the match room
        room_name = f"match_{match_id}"
        
        # Send to sender
        emit('new_message', sender_message_data)
        
        # Send to other users in the room (excluding sender)
        emit('new_message', recipient_message_data, room=room_name, include_self=False)
        
        # Also send to all users involved in the match (for notifications when outside chat)
        # Get the other user involved in this match
        other_user_id = None
        if match.dog_one_id in user_dog_ids:
            # Current user owns dog_one, so other user owns dog_two
            other_dog = Dog.query.get(match.dog_two_id)
            if other_dog:
                other_user_id = other_dog.owner_id
        else:
            # Current user owns dog_two, so other user owns dog_one
            other_dog = Dog.query.get(match.dog_one_id)
            if other_dog:
                other_user_id = other_dog.owner_id
        
        # Send notification to the other user if they're online
        if other_user_id and other_user_id in active_users:
            logger.info(f"📱 Sending notification to user {other_user_id} for match {match_id}")
            for socket_id in active_users[other_user_id]:
                emit('new_message', recipient_message_data, room=socket_id)
                logger.info(f"📱 Sent notification to socket {socket_id}")
        else:
            logger.info(f"📱 User {other_user_id} not online or not found in active_users")
        
        logger.info(f"Message sent in match {match_id} by user {user.id}")
        
        # Send confirmation to sender
        emit('message_sent', {
            'message_id': message.id,
            'status': 'success'
        })
        
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        emit('error', {'message': 'Failed to send message'})
        db.session.rollback()

@socketio.on('typing')
def handle_typing(data):
    """Handle typing indicators"""
    user = authenticate_user()
    if not user:
        return False
    
    match_id = data.get('match_id')
    is_typing = data.get('is_typing', False)
    
    if not match_id:
        return
    
    # Verify user is part of this match
    match = Match.query.get(match_id)
    if not match:
        return
    
    user_dog_ids = [dog.id for dog in user.dogs]
    if match.dog_one_id not in user_dog_ids and match.dog_two_id not in user_dog_ids:
        return
    
    # Broadcast typing indicator to other users in the match
    room_name = f"match_{match_id}"
    emit('user_typing', {
        'user_id': user.id,
        'username': user.username,
        'first_name': user.first_name,
        'is_typing': is_typing,
        'match_id': match_id
    }, room=room_name, include_self=False)

@socketio.on('read_receipt')
def handle_read_receipt(data):
    """Handle read receipts for messages"""
    user = authenticate_user()
    if not user:
        return False
    
    message_id = data.get('message_id')
    if not message_id:
        return
    
    try:
        # Get message
        message = Message.query.get(message_id)
        if not message:
            return
        
        # Check if user is part of the match
        user_dog_ids = [dog.id for dog in user.dogs]
        if (message.match.dog_one_id not in user_dog_ids and 
            message.match.dog_two_id not in user_dog_ids):
            return
        
        # Mark as read (only if not sent by current user)
        if message.sender_user_id != user.id:
            message.mark_as_read()
            
            # Broadcast read receipt
            room_name = f"match_{message.match_id}"
            emit('message_read', {
                'message_id': message_id,
                'read_by_user_id': user.id,
                'read_at': message.read_at.isoformat() if message.read_at else None
            }, room=room_name)
            
            logger.info(f"Message {message_id} marked as read by user {user.id}")
    
    except Exception as e:
        logger.error(f"Error handling read receipt: {str(e)}")

@socketio.on('get_online_users')
def handle_get_online_users():
    """Get list of currently online users"""
    user = authenticate_user()
    if not user:
        return False
    
    online_users = []
    for user_id in active_users.keys():
        online_user = User.query.get(user_id)
        if online_user:
            online_users.append({
                'user_id': online_user.id,
                'username': online_user.username,
                'first_name': online_user.first_name,
                'last_name': online_user.last_name
            })
    
    emit('online_users', {
        'users': online_users,
        'count': len(online_users)
    })

@socketio.on('ping')
def handle_ping():
    """Handle ping for connection testing"""
    emit('pong', {'timestamp': datetime.utcnow().isoformat()})
