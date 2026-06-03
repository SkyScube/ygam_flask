import os
import jwt
from flask import request
from flask_socketio import emit, join_room, leave_room

from src.extensions import socketio
from src.models import User
from src.services.chat_service import persist_message, mark_delivered


def _auth_user_from_cookie():
    """Resolves the authenticated user from the access_token cookie."""
    token = request.cookies.get('access_token')
    if not token:
        return None
    try:
        data = jwt.decode(token, os.getenv('JWT_SECRET'), algorithms=['HS256'])
        if data.get('type') != 'access':
            return None
        return User.query.get(data['user_id'])
    except jwt.InvalidTokenError:
        return None


def register_socket_events(sio):

    @sio.on('connect')
    def on_connect():
        user = _auth_user_from_cookie()
        if not user:
            return False  # Refuse connection

        join_room(f'user:{user.id}')
        emit('connected', {'user_id': user.id, 'username': user.Username})

    @sio.on('disconnect')
    def on_disconnect():
        user = _auth_user_from_cookie()
        if user:
            leave_room(f'user:{user.id}')

    @sio.on('send_message')
    def on_send_message(data):
        user = _auth_user_from_cookie()
        if not user:
            emit('error', {'message': 'Not authenticated'})
            return

        receiver_id = data.get('to')
        content = (data.get('content') or '').strip()

        if not receiver_id or not content:
            emit('error', {'message': 'Missing to or content'})
            return

        receiver = User.query.get(receiver_id)
        if not receiver:
            emit('error', {'message': 'Recipient not found'})
            return

        msg = persist_message(user.id, receiver_id, content)

        # Send to receiver's room
        sio.emit('new_message', msg, to=f'user:{receiver_id}')

        # Confirm to sender
        emit('message_sent', msg)

        mark_delivered(msg['id'])
