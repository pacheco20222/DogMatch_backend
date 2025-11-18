"""
WSGI Entry Point for DogMatch Backend
Handles gevent monkey patching before app initialization
"""

# ============================================================================
# CRITICAL: Monkey patch MUST happen before ANY other imports
# ============================================================================
from gevent import monkey
monkey.patch_all()

# Now we can safely import the app
from app import create_app, socketio

# Create the Flask application
app = create_app()

if __name__ == "__main__":
    # Run with socketio for development
    socketio.run(app, host='0.0.0.0', port=5002, debug=False)
