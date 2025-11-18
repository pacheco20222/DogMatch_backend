"""
Local Development Server Entry Point
For production, use wsgi.py instead
"""

# Monkey patch for gevent compatibility
# Take note of the wsgi.py file, it is the entry point for the production server
from gevent import monkey
monkey.patch_all()

from app import create_app, socketio
import os

app = create_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5002))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Run with socketio
    socketio.run(
        app,
        host='0.0.0.0',
        port=port,
        debug=debug,
        use_reloader=debug,
        log_output=True
    )