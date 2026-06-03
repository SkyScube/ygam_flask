"""
SocketIO event handlers
"""
from flask_socketio import emit, join_room, leave_room
from . import socketio

@socketio.on('connect')
def handle_connect():
    """Client connected to WebSocket"""
    print(f"✅ Client connected")
    emit('connection_response', {'status': 'connected'})

@socketio.on('disconnect')
def handle_disconnect():
    """Client disconnected"""
    print(f"❌ Client disconnected")

@socketio.on('auth_init')
def handle_auth_init(data):
    """Test authentication initialization"""
    print(f"📥 Received auth_init: {data}")
    emit('auth_response', {
        'status': 'success',
        'message': 'Authentication received',
        'data': data
    })

@socketio.on('test_message')
def handle_test_message(data):
    """Simple test message"""
    print(f"📨 Test message: {data}")
    emit('test_response', {'echo': data, 'status': 'received'})
