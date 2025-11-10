"""
Gemini AI Service for DogMatch
Integrates Google's Gemini API to provide AI-powered assistance to users
"""

import os
import logging
import google.generativeai as genai
from typing import Optional

logger = logging.getLogger(__name__)

# Configure Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    logger.info("Gemini AI service configured successfully")
else:
    logger.warning("GEMINI_API_KEY not found - AI assistant will not be available")


# DogMatch context for AI - helps AI understand the app
DOGMATCH_CONTEXT = """
You are a friendly and helpful AI assistant for DogMatch, a dog matching and social platform.

**About DogMatch:**
DogMatch is like Tinder, but for dogs! It helps dog owners find playdates and companions for their furry friends.

**Key Features:**

1. **Dog Profiles** (REQUIRED TO USE APP):
   - Users MUST create at least one dog profile before using any features
   - Without a dog profile, users cannot swipe, match, or chat
   - To create a dog: Tap the DOG ICON (🐕) at the bottom navigation bar
   - Add photos, breed, age, size, temperament, and a fun bio
   - Each dog can have multiple photos
   - Users can have multiple dogs and switch between them

2. **Matching System** (Swipe Feature):
   - Browse dogs from other users (not location-based, just all users)
   - THREE swipe actions:
     * Swipe RIGHT (❤️) = Like this dog
     * Swipe LEFT (✖️) = Pass/Skip
     * Swipe UP (⭐) = Super Like (shows extra interest!)
   - IMPORTANT: When you swipe right, the OTHER user receives a notification
   - The OTHER user must ACCEPT your match request
   - Only when BOTH users accept = MATCH! 🎉
   - No match = no chat possible

3. **Real-time Chat**:
   - You can ONLY chat with matched dog owners
   - A match is required before any conversation can start
   - After matching, owners can chat instantly in real-time
   - Arrange playdates, share tips, become friends
   - Find your conversations in the CHATS tab

4. **Community Events**:
    - Local dog meetups, training classes, adoption events
    - USERS can register/attend events and RSVP via the Events tab
    - NOTE: Only platform admins and verified shelters/organizers can create events
      (regular users cannot create events)
    - See which other dogs are attending
    - Great way to meet dogs in your area!

**Your Role:**
- Always mention that a dog profile is REQUIRED before using features
- When explaining swipes, mention all THREE options (left, right, UP for super like)
- Clarify that matches need BOTH users to accept (it's not automatic)
- Remind users that chat requires a match first
- Direct users to tap the DOG ICON in bottom navigation to create dogs
- Keep responses under 150 words (be concise and actionable!)
- Use dog emojis when appropriate 🐕🐾❤️⭐
- Be encouraging, positive, and specific
- Give exact navigation steps when possible (e.g., "Go to Chats tab", "Tap dog icon")

**Tone:**
Friendly, warm, enthusiastic about dogs, helpful with specific step-by-step guidance.
"""


def ask_gemini(question: str, context_type: str = 'general') -> str:
    """
    Ask Gemini AI a question about DogMatch
    
    Args:
        question: User's question
        context_type: Type of question (general, profile, matching, events, chat)
    
    Returns:
        AI-generated response as string
    
    Raises:
        ValueError: If API key is not configured
        Exception: If API call fails
    """
    
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not configured. Please add it to your .env file.")
    
    try:
        # Initialize the model. Use a currently available Gemini model name.
        # Prefer the 'gemini-flash-latest' alias so we get the most up-to-date flash model.
        model = genai.GenerativeModel('models/gemini-flash-latest')

        # Add context-specific guidance
        context_guidance = _get_context_guidance(context_type)
        
        # Combine context + guidance + question
        full_prompt = f"{DOGMATCH_CONTEXT}\n\n{context_guidance}\n\nUser Question: {question}\n\nYour Answer:"
        
        logger.info(f"Sending question to Gemini (context: {context_type}): {question[:50]}...")
        
        # Generate response
        response = model.generate_content(full_prompt)
        
        # Extract text from response
        answer = response.text.strip()
        
        logger.info(f"Gemini response received: {len(answer)} characters")
        
        return answer
        
    except Exception as e:
        logger.error(f"Gemini API error: {str(e)}")
        
        # Return friendly fallback message
        return _get_fallback_response(context_type, question)


def _get_context_guidance(context_type: str) -> str:
    """
    Get additional guidance based on question context
    """
    guidance = {
        'profile': """
Focus on: That dog profiles are REQUIRED to use the app, how to create them by tapping the 
DOG ICON in bottom navigation, what information to include, uploading photos, editing profiles, 
managing multiple dogs.
        """,
        
        'matching': """
Focus on: The THREE swipe actions (left/pass, right/like, UP/super like), that matches need 
BOTH users to accept, how to see pending match requests, tips for getting more matches.
        """,
        
    'events': """
Focus on: How to find events, how to register/attend events, how to RSVP, what types of
events exist, event notifications, and that only admins/verified shelters can create events.
Tell users they can register to events from the Events tab; creating events is restricted
to admins and shelters.
    """,
        
        'chat': """
Focus on: That a MATCH is required before chatting, how to access messages in the Chats tab, 
sending messages, chat etiquette, how to continue conversations.
        """,
        
        'general': """
Focus on: Overall app usage, getting started, main features, user types, 
general troubleshooting, account management.
        """
    }
    
    return guidance.get(context_type, guidance['general'])


def _get_fallback_response(context_type: str, question: str) -> str:
    """
    Return helpful fallback response when AI service fails
    """
    fallback_responses = {
        'profile': """
⚠️ You MUST create a dog profile before using DogMatch!

To create your dog:
1. Tap the DOG ICON (🐕) at the bottom navigation bar
2. Tap the '+' button
3. Add a photo (required)
4. Fill in your dog's name, breed, age, size
5. Write a fun bio!
6. Tap 'Save'

You can add multiple dogs and edit them anytime! 🐕
        """,
        
        'matching': """
DogMatch uses a THREE-way swipe system:
- Swipe RIGHT (❤️) = Like this dog
- Swipe LEFT (✖️) = Pass/Skip  
- Swipe UP (⭐) = Super Like!

When you like someone, THEY receive a notification and must accept.
Only when BOTH accept = MATCH! 🎉

Then you can chat and arrange playdates! 🐾
        """,
        
    'events': """
Community Events let you:
- Find dog meetups, training classes, and adoption events
- Register / RSVP to attend events from the Events tab
- See which dogs are going

Note: Only admins and verified shelters can create events. If you'd like to
host an event, contact support or a shelter/organizer to request creation.

Check the 'Events' tab to see what's happening near you! 📅
    """,
        
        'chat': """
⚠️ You can ONLY chat with matched dogs!

After you and another user BOTH accept the match:
1. Go to the 'Chats' tab
2. Select your conversation
3. Start chatting in real-time!
4. Arrange playdates, share tips, make friends

No match = no chat possible. Keep swiping to find matches! 💬
        """,
        
        'general': """
Welcome to DogMatch! 🐕❤️

**Getting Started:**
1. FIRST: Create a dog profile (tap DOG ICON 🐕 at bottom)
2. Browse dogs from other users and swipe (left/right/up!)
3. When BOTH users accept = Match! 🎉
4. Chat with your matches in the Chats tab
5. Join community events to meet dogs!

⚠️ You need a dog profile before you can swipe or chat!

Need more help? Feel free to ask specific questions!
        """
    }
    
    return fallback_responses.get(context_type, fallback_responses['general'])


def check_service_health() -> dict:
    """
    Check if Gemini AI service is properly configured and available
    
    Returns:
        Dictionary with service status
    """
    if not GEMINI_API_KEY:
        return {
            'status': 'unavailable',
            'provider': 'gemini',
            'error': 'API key not configured',
            'message': 'GEMINI_API_KEY environment variable is not set'
        }
    
    try:
        # Try a simple test request
        # Use a supported model alias to validate service availability
        model = genai.GenerativeModel('models/gemini-flash-latest')
        response = model.generate_content("Say 'OK' if you can hear me")

        if response.text:
            return {
                'status': 'available',
                'provider': 'gemini',
                'model': 'models/gemini-flash-latest',
                'message': 'AI Assistant is ready to help!'
            }
        else:
            raise Exception("Empty response from Gemini")
            
    except Exception as e:
        logger.error(f"Gemini health check failed: {str(e)}")
        return {
            'status': 'error',
            'provider': 'gemini',
            'error': str(e),
            'message': 'AI Assistant is temporarily unavailable'
        }