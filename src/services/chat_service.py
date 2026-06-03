from datetime import datetime
from sqlalchemy import or_, and_
from src.models import db, User, Message
from src.utils import generate_cuid
from src.logger import logger


def get_conversations(user):
    """
    Returns the list of users the given user has exchanged messages with,
    along with the last message for each conversation.
    Designed so that adding a Group/Conversation table later only changes this service.
    """
    sent = (
        db.session.query(Message.Id_user_receiver.label('other_id'))
        .filter(Message.Id_user_sender == user.id)
    )
    received = (
        db.session.query(Message.Id_user_sender.label('other_id'))
        .filter(Message.Id_user_receiver == user.id)
    )
    contact_ids = {row.other_id for row in sent.union(received).all()}
    logger.debug("get_conversations: user={} has {} contacts", user.id, len(contact_ids))

    conversations = []
    for contact_id in contact_ids:
        contact = User.query.get(contact_id)
        if not contact:
            continue

        last_msg = (
            Message.query
            .filter(
                or_(
                    and_(Message.Id_user_sender == user.id, Message.Id_user_receiver == contact_id),
                    and_(Message.Id_user_sender == contact_id, Message.Id_user_receiver == user.id),
                )
            )
            .order_by(Message.Date.desc())
            .first()
        )

        conversations.append({
            'contact_id': contact.id,
            'contact_username': contact.Username,
            'last_message': last_msg.Content if last_msg else '',
            'last_message_date': last_msg.Date.isoformat() if last_msg else None,
        })

    conversations.sort(key=lambda c: c['last_message_date'] or '', reverse=True)
    return conversations


def get_message_history(user, other_user_id, limit=50):
    logger.debug("get_message_history: user={} with other={} limit={}", user.id, other_user_id, limit)
    messages = (
        Message.query
        .filter(
            or_(
                and_(Message.Id_user_sender == user.id, Message.Id_user_receiver == other_user_id),
                and_(Message.Id_user_sender == other_user_id, Message.Id_user_receiver == user.id),
            )
        )
        .order_by(Message.Date.asc())
        .limit(limit)
        .all()
    )
    return [_serialize_message(msg) for msg in messages]


def persist_message(sender_id, receiver_id, content_text):
    logger.info("persist_message: sender={} -> receiver={}", sender_id, receiver_id)
    msg = Message(
        id=generate_cuid(),
        Id_user_sender=sender_id,
        Id_user_receiver=receiver_id,
        Content=content_text,
        Is_delivered=False,
        Date=datetime.utcnow(),
    )
    db.session.add(msg)
    db.session.commit()
    return _serialize_message(msg)


def mark_delivered(message_id):
    msg = Message.query.get(message_id)
    if msg:
        msg.Is_delivered = True
        db.session.commit()
        logger.debug("mark_delivered: message={}", message_id)


def search_users(query, exclude_user_id, limit=10):
    logger.debug("search_users: query='{}' exclude={}", query, exclude_user_id)
    return (
        User.query
        .filter(User.Username.ilike(f'{query}%'), User.id != exclude_user_id)
        .limit(limit)
        .all()
    )


def _serialize_message(msg):
    return {
        'id': msg.id,
        'sender_id': msg.Id_user_sender,
        'receiver_id': msg.Id_user_receiver,
        'content': msg.Content,
        'date': msg.Date.isoformat(),
        'is_delivered': msg.Is_delivered,
    }
