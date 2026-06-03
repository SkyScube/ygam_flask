import os
import jwt
from flask import request
from flask_socketio import emit, join_room, leave_room

from src.models import User
from src.services.chat_service import persist_message, mark_delivered
from src.logger import logger

# Maps socket session id -> user_id (avoids relying on flask session with manage_session=False)
connected_users = {}


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
            logger.warning("Socket connect refused: no valid access_token (sid={})", request.sid)
            return False

        connected_users[request.sid] = user.id
        join_room(f'user:{user.id}')
        logger.info("Socket connected: user={} sid={}", user.Username, request.sid)
        emit('connected', {'user_id': user.id, 'username': user.Username})

    @sio.on('disconnect')
    def on_disconnect():
        user_id = connected_users.pop(request.sid, None)
        if user_id:
            leave_room(f'user:{user_id}')
            logger.info("Socket disconnected: user_id={} sid={}", user_id, request.sid)

    @sio.on('send_message')
    def on_send_message(data):
        user_id = connected_users.get(request.sid)
        if not user_id:
            logger.warning("send_message from unauthenticated socket sid={}", request.sid)
            emit('error', {'message': 'Not authenticated'})
            return

        receiver_id = data.get('to')
        content = (data.get('content') or '').strip()

        if not receiver_id or not content:
            logger.warning("send_message missing fields: user={} to={}", user_id, receiver_id)
            emit('error', {'message': 'Missing to or content'})
            return

        receiver = User.query.get(receiver_id)
        if not receiver:
            logger.warning("send_message: recipient not found user_id={}", receiver_id)
            emit('error', {'message': 'Recipient not found'})
            return

        logger.debug("send_message: {} -> {}", user_id, receiver_id)
        msg = persist_message(user_id, receiver_id, content)

        sio.emit('new_message', msg, to=f'user:{receiver_id}')
        emit('message_sent', msg)
        mark_delivered(msg['id'])
