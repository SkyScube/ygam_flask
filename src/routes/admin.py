from flask import Blueprint, render_template, request, jsonify
from src.decorator import jwt_required, admin_required
from src.models import db, Message, User
from src.logger import logger

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.get('/messages')
@jwt_required
@admin_required
def delivered_messages():
    msgs = (
        Message.query
        .filter_by(Is_delivered=True)
        .order_by(Message.Date.desc())
        .all()
    )
    user_ids = {m.Id_user_sender for m in msgs} | {m.Id_user_receiver for m in msgs}
    users = {u.id: u.Username for u in User.query.filter(User.id.in_(user_ids)).all()}

    rows = [
        {
            'id': m.id,
            'sender': users.get(m.Id_user_sender, m.Id_user_sender),
            'receiver': users.get(m.Id_user_receiver, m.Id_user_receiver),
            'content': m.Content,
            'date': m.Date.strftime('%Y-%m-%d %H:%M:%S'),
        }
        for m in msgs
    ]
    logger.info("admin/messages: accessed by user={}", request.current_user.id)
    return render_template('admin/messages.html', messages=rows, current_user=request.current_user)


@admin_bp.delete('/messages/<string:message_id>')
@jwt_required
@admin_required
def delete_message(message_id):
    msg = Message.query.get(message_id)
    if not msg:
        return jsonify({'message': 'Message introuvable'}), 404
    db.session.delete(msg)
    db.session.commit()
    logger.info("admin: message={} physically deleted by user={}", message_id, request.current_user.id)
    return jsonify({'message': 'Supprimé'}), 200
