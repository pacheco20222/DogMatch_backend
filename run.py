import os 
from app import create_app, socketio

app = create_app()

if __name__ == "__main__":
    debug_mode = os.environ.get("FLASK_DEBUG", "True").lower() == "true"
    port = int(os.environ.get("PORT", 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    
    print("Backend is starting")
    print(f"The backend is running on http://{host}:{port}")

    socketio.run(
        app,
        host=host,
        port=port,
        debug=debug_mode,
        allow_unsafe_werkzeug=True
    )