from datetime import datetime
from sqlalchemy import or_, and_
from src.models import db, User, Message
from src.client_models import Contact, Conversation, LocalMessage
from src.utils import generate_cuid
from src.logger import logger


def get_conversations(user):
    """
    Read conversations from the client SQLite DB (permanent store).
    MySQL only holds in-transit messages, so history must come from SQLite.
    """
    contacts = Contact.query.filter_by(owner_user_id=user.id).all()
    logger.debug("get_conversations: user={} has {} contacts", user.id, len(contacts))

    conversations = []
    for contact in contacts:
        conv = Conversation.query.filter_by(contact_id=contact.contact_id).first()
        if not conv:
            continue
        conversations.append({
            'contact_id': contact.server_user_id,
            'contact_username': contact.username,
            'last_message': conv.last_message_preview_encrypted or '',
            'last_message_date': conv.last_message_at.isoformat() if conv.last_message_at else None,
            'unread_count': conv.unread_count,
        })

    conversations.sort(key=lambda c: c['last_message_date'] or '', reverse=True)
    return conversations


def get_message_history(user, other_user_id, limit=50):
    """
    Read message history from the client SQLite DB.
    """
    logger.debug("get_message_history: user={} with other={} limit={}", user.id, other_user_id, limit)
    contact = Contact.query.filter_by(
        owner_user_id=user.id, server_user_id=other_user_id
    ).first()
    if not contact:
        return []

    conv = Conversation.query.filter_by(contact_id=contact.contact_id).first()
    if not conv:
        return []

    messages = (
        LocalMessage.query
        .filter_by(conversation_id=conv.conversation_id)
        .order_by(LocalMessage.sent_at.asc())
        .limit(limit)
        .all()
    )
    return [_serialize_local_message(m, user.id, other_user_id) for m in messages]


def persist_message(sender_id, receiver_id, content_text):
    """
    Store message temporarily in MySQL (relay) + sender's SQLite (permanent outgoing copy).
    The receiver's SQLite copy is written only on confirmed delivery via deliver_message().
    """
    logger.info("persist_message: sender={} -> receiver={}", sender_id, receiver_id)
    now = datetime.utcnow()
    msg = Message(
        id=generate_cuid(),
        Id_user_sender=sender_id,
        Id_user_receiver=receiver_id,
        Content=content_text,
        Is_delivered=False,
        Date=now,
    )
    db.session.add(msg)
    db.session.commit()

    from src.services.client_service import store_outgoing
    receiver = User.query.get(receiver_id)
    if receiver:
        store_outgoing(msg.id, sender_id, receiver, content_text, now)
        db.session.commit()

    return _serialize_message(msg)


def deliver_message(message_id):
    """
    Called when the receiver has confirmed receipt of a message.
    Writes the incoming copy to the receiver's SQLite DB, then deletes
    the message from MySQL (server is relay only — no permanent storage).
    """
    msg = Message.query.get(message_id)
    if not msg:
        return

    from src.services.client_service import store_incoming
    sender = User.query.get(msg.Id_user_sender)
    if sender:
        store_incoming(msg.id, sender, msg.Id_user_receiver, msg.Content, msg.Date)

    msg.Is_delivered = True
    db.session.commit()
    logger.info("deliver_message: msg={} delivered and removed from server", message_id)


def get_pending_messages(user_id):
    """Return all undelivered messages waiting for this user on the server."""
    msgs = (
        Message.query
        .filter_by(Id_user_receiver=user_id, Is_delivered=False)
        .order_by(Message.Date.asc())
        .all()
    )
    logger.debug("get_pending_messages: {} pending for user={}", len(msgs), user_id)
    return [_serialize_message(m) for m in msgs]


def mark_delivered(message_id):
    """Legacy alias kept for tests — delegates to deliver_message."""
    deliver_message(message_id)


def search_users(query, exclude_user_id, limit=10):
    logger.debug("search_users: query='{}' exclude={}", query, exclude_user_id)
    return (
        User.query
        .filter(User.Username.ilike(f'{query}%'), User.id != exclude_user_id)
        .limit(limit)
        .all()
    )


def _serialize_message(msg):
    """Serialize a MySQL transit Message (used internally before delivery)."""
    return {
        'id': msg.id,
        'sender_id': msg.Id_user_sender,
        'receiver_id': msg.Id_user_receiver,
        'content': msg.Content,
        'date': msg.Date.isoformat(),
        'is_delivered': msg.Is_delivered,
    }


def _serialize_local_message(local_msg, owner_id, peer_id):
    """Serialize a SQLite LocalMessage for the API response."""
    if local_msg.direction == 'outgoing':
        sender_id, receiver_id = owner_id, peer_id
    else:
        sender_id, receiver_id = peer_id, owner_id
    return {
        'id': local_msg.server_message_id or local_msg.local_message_id,
        'sender_id': sender_id,
        'receiver_id': receiver_id,
        'content': local_msg.encrypted_content,
        'date': local_msg.sent_at.isoformat() if local_msg.sent_at else None,
        'is_delivered': local_msg.status in ('sent', 'received', 'read'),
        'direction': local_msg.direction,
    }
