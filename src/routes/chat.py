from flask import Blueprint, render_template, jsonify, request
from src.decorator import jwt_required
from src.models import User
from src.services.chat_service import get_conversations, get_message_history, search_users

chat_bp = Blueprint('chat', __name__)


@chat_bp.route('/chat')
@jwt_required
def chat_page():
    return render_template('chat/chat.html', current_user=request.current_user)


@chat_bp.get('/api/conversations')
@jwt_required
def api_conversations():
    convs = get_conversations(request.current_user)
    return jsonify(convs)


@chat_bp.get('/api/messages/<string:other_user_id>')
@jwt_required
def api_messages(other_user_id):
    history = get_message_history(request.current_user, other_user_id)
    return jsonify(history)


@chat_bp.get('/api/users/search')
@jwt_required
def api_search_users():
    q = request.args.get('q', '').strip()
    if len(q) < 2:
        return jsonify([])
    users = search_users(q, exclude_user_id=request.current_user.id)
    return jsonify([{'id': u.id, 'username': u.Username} for u in users])
