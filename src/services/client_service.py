"""
Client-side SQLite simulation service  —  PDF §3.2

Called by chat_service after every MySQL write to mirror the message
into the local client DB (Contact → Conversation → LocalMessage).
In a real app this logic runs inside the client device; here it runs
server-side to simulate the client store.
"""

from datetime import datetime
from src.models import db, User
from src.client_models import Contact, Conversation, LocalMessage
from src.utils import generate_cuid
from src.logger import logger


def _get_or_create_contact(owner_user_id: str, server_user: User) -> Contact:
    """Return the Contact entry for owner→server_user, creating it if absent."""
    contact = Contact.query.filter_by(
        owner_user_id=owner_user_id,
        server_user_id=server_user.id,
    ).first()

    if not contact:
        contact = Contact(
            contact_id=generate_cuid(),
            owner_user_id=owner_user_id,
            server_user_id=server_user.id,
            username=server_user.Username,
            display_name=server_user.Username,
        )
        db.session.add(contact)
        db.session.flush()  # get contact_id before conversation FK
        logger.debug("client_service: created Contact owner={} peer={}", owner_user_id, server_user.id)

    return contact


def _get_or_create_conversation(contact: Contact) -> Conversation:
    """Return the Conversation for this contact, creating it if absent."""
    conv = Conversation.query.filter_by(contact_id=contact.contact_id).first()

    if not conv:
        conv = Conversation(
            conversation_id=generate_cuid(),
            contact_id=contact.contact_id,
            created_at=datetime.utcnow(),
        )
        db.session.add(conv)
        db.session.flush()
        logger.debug("client_service: created Conversation for contact={}", contact.contact_id)

    return conv


def _update_conversation(conv: Conversation, preview: str, at: datetime, incoming: bool):
    conv.last_message_at = at
    conv.last_message_preview_encrypted = preview  # plain text for POC
    if incoming:
        conv.unread_count = (conv.unread_count or 0) + 1


def store_outgoing(server_message_id: str, sender_id: str, receiver: User,
                   content: str, sent_at: datetime):
    """Write the outgoing copy to the sender's client DB."""
    try:
        contact = _get_or_create_contact(sender_id, receiver)
        conv = _get_or_create_conversation(contact)
        _update_conversation(conv, content, sent_at, incoming=False)

        local_msg = LocalMessage(
            local_message_id=generate_cuid(),
            conversation_id=conv.conversation_id,
            server_message_id=server_message_id,
            encrypted_content=content,
            algorithm='none',
            direction='outgoing',
            status='sent',
            sent_at=sent_at,
        )
        db.session.add(local_msg)
        logger.debug("client_service: stored outgoing msg={} conv={}", server_message_id, conv.conversation_id)
    except Exception:
        logger.exception("client_service: failed to store outgoing msg={}", server_message_id)


def store_incoming(server_message_id: str, sender: User, receiver_id: str,
                   content: str, sent_at: datetime):
    """Write the incoming copy to the receiver's client DB."""
    try:
        contact = _get_or_create_contact(receiver_id, sender)
        conv = _get_or_create_conversation(contact)
        _update_conversation(conv, content, sent_at, incoming=True)

        local_msg = LocalMessage(
            local_message_id=generate_cuid(),
            conversation_id=conv.conversation_id,
            server_message_id=server_message_id,
            encrypted_content=content,
            algorithm='none',
            direction='incoming',
            status='received',
            sent_at=sent_at,
            received_at=datetime.utcnow(),
        )
        db.session.add(local_msg)
        logger.debug("client_service: stored incoming msg={} conv={}", server_message_id, conv.conversation_id)
    except Exception:
        logger.exception("client_service: failed to store incoming msg={}", server_message_id)
