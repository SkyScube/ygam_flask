"""
SocketIO initialization and configuration
"""
from flask_socketio import SocketIO

# Create SocketIO instance (will be initialized with app later)
socketio = SocketIO(
    cors_allowed_origins="*",  # Pour le dev, à restreindre en prod
    logger=True,
    engineio_logger=True
)

def init_socketio(app):
    """Initialize SocketIO with the Flask app"""
    socketio.init_app(app)
    
    # Import event handlers after socketio is initialized
    from . import events
    
    return socketio
