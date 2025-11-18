from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging

# AI agent Using gemini
# comment 
ai_bp = Blueprint('ai_assistant', __name__)
logger = logging.getLogger(__name__)

@ai_bp.route('/ask', methods=['POST'])
@jwt_required()
def ask_assistant():
    """
    AI Assistant endpoint - helps users understand DogMatch features
    
    Request body:
    {
        "question": "How do I create a dog profile?",
        "context": "profile"  // optional: profile, matching, events, chat, general
    }
    
    Response:
    {
        "answer": "AI generated response...",
        "tokens_used": 150
    }
    """
    try:
        #Get the current user
        current_user_id = get_jwt_identity()
        
        # Request data
        data = request.get_json()
        question = data.get('question', '').strip()
        context_type = data.get('context', 'general')
        
        # Validate
        if not question:
            return jsonify({
                'error': 'Question required',
                'message': 'Please provide a question for the AI assistant'
            }), 400
            
        if len(question) > 500:
            return jsonify({
                'error': 'Question too long',
                'message': 'Please keep questions under 500 characters'
            }), 400

        logger.info(f"AI assistant request from user {current_user_id}: {question[:50]}...")

        from app.services.gemini_service import ask_gemini

        response = ask_gemini(question, context_type)
        logger.info(f"AI assistant generated a response: {len(response)} characters")

        return jsonify({
            'answer' : response,
            'tokens_used' : len(question.split()) + len(response.split()),
            'context': context_type
        }), 200
        
    except ValueError as error:
        logger.error(f"AI assistant configuration error: {str(error)}")
        return jsonify({
            'error' : 'AI assistant error',
            'message' : 'Failed to generate a response. Please try again.'
        }), 500
        
@ai_bp.route('/quick-actions', methods=['GET'])
@jwt_required()
def get_quick_actions():
    """
    Get predefined quick action buttons for AI assistant
    
    Response:
    {
        "actions": [
            {
                "id": "about",
                "label": "What is DogMatch?",
                "icon": "info",
                "context": "general"
            },
            ...
        ]
    }
    """
    try:
        quick_actions = [
            {
                'id': 'about',
                'label': 'What is DogMatch?',
                'icon': 'info',
                'context': 'general',
                'question': 'What is DogMatch and how does it work?'
            },
            {
                'id': 'create_dog',
                'label': 'How do I create a dog profile?',
                'icon': 'plus',
                'context': 'profile',
                'question': 'How do I create a dog profile? What information do I need?'
            },
            {
                'id': 'matching',
                'label': 'How does matching work?',
                'icon': 'heart',
                'context': 'matching',
                'question': 'How does the dog matching system work? How do I get matches?'
            },
            {
                'id': 'events',
                'label': 'How do events work?',
                'icon': 'calendar',
                'context': 'events',
                'question': 'How do community events work? How do I join or create events?'
            },
            {
                'id': 'chat',
                'label': 'How do I chat with matches?',
                'icon': 'message',
                'context': 'chat',
                'question': 'How do I chat with my matches? Where do I find my messages?'
            }
        ]
        
        return jsonify({
            'actions' : quick_actions
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching quick actions: {str(e)}")
        return jsonify({
            'error' : 'Failed to load quick actions',
            'message' : str(e)
        }), 500
        

@ai_bp.route('/health', methods=['GET'])
def health_check():
    """
    Check if AI assistant service is available
    
    Response:
    {
        "status": "available",
        "provider": "gemini",
        "model": "gemini-1.5-flash"
    }
    """
    try:
        from app.services.gemini_service import check_service_health
        
        health = check_service_health()
        
        return jsonify(health), 200
        
    except Exception as e:
        logger.error(f"AI service health check failed: {str(e)}")
        return jsonify({
            'status': 'unavailable',
            'error': str(e)
        }), 503        