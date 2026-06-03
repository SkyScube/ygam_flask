"""
CLIENT-SIDE SIMULATION DATABASE  —  PDF §3.2

In the real app these tables live in IndexedDB inside the browser.
Here we simulate them in a separate SQLite file via Flask-SQLAlchemy bind 'client'
so the server MySQL schema stays completely untouched.

__bind_key__ = 'client' routes every query for these models to the SQLite DB
defined in config.py under SQLALCHEMY_BINDS['client'].
"""

from datetime import datetime
from sqlalchemy import Index, UniqueConstraint
from src.models import db   # same SQLAlchemy instance, separate bind


class Contact(db.Model):
    """PDF: Contact — local address book entry."""
    __bind_key__ = 'client'
    __tablename__ = 'Contact'

    contact_id     = db.Column(db.String(191), primary_key=True)
    owner_user_id  = db.Column(db.String(191), nullable=False)   # "this client"
    server_user_id = db.Column(db.String(191), nullable=False)   # FK to server User.id (soft ref)
    username       = db.Column(db.String(191), nullable=False)
    display_name   = db.Column(db.String(191), nullable=True)
    public_key     = db.Column(db.Text, nullable=True)           # E2EE: RSA/EC pubkey
    last_seen_at   = db.Column(db.DateTime, nullable=True)
    is_blocked     = db.Column(db.Boolean, default=False, nullable=False)

    conversations  = db.relationship('Conversation', back_populates='contact', cascade='all, delete-orphan')

    __table_args__ = (
        UniqueConstraint('owner_user_id', 'server_user_id', name='uq_owner_server_user'),
    )


class Conversation(db.Model):
    """PDF: Conversation — one per Contact (DM); groups add a group_id later."""
    __bind_key__ = 'client'
    __tablename__ = 'Conversation'

    conversation_id                = db.Column(db.String(191), primary_key=True)
    contact_id                     = db.Column(db.String(191), db.ForeignKey('Contact.contact_id'), nullable=False)
    created_at                     = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_message_at                = db.Column(db.DateTime, nullable=True)
    last_message_preview_encrypted = db.Column(db.Text, nullable=True)   # E2EE preview; POC: plain text
    unread_count                   = db.Column(db.Integer, default=0, nullable=False)
    is_archived                    = db.Column(db.Boolean, default=False, nullable=False)

    contact  = db.relationship('Contact', back_populates='conversations')
    messages = db.relationship('LocalMessage', back_populates='conversation', cascade='all, delete-orphan')


class LocalMessage(db.Model):
    """PDF: LocalMessage — local copy of a message."""
    __bind_key__ = 'client'
    __tablename__ = 'LocalMessage'

    local_message_id  = db.Column(db.String(191), primary_key=True)
    conversation_id   = db.Column(db.String(191), db.ForeignKey('Conversation.conversation_id'), nullable=False)
    server_message_id = db.Column(db.String(191), nullable=True)          # NULL until server ACK
    encrypted_content = db.Column(db.Text, nullable=False)                 # POC: plain text
    nonce_iv          = db.Column(db.String(191), nullable=True)           # E2EE: AES-GCM nonce
    algorithm         = db.Column(db.String(64), default='none', nullable=False)
    direction         = db.Column(db.String(16), nullable=False)           # incoming | outgoing
    status            = db.Column(db.String(16), default='pending', nullable=False)
    # status: pending | sent | received | read
    sent_at           = db.Column(db.DateTime, nullable=True)
    received_at       = db.Column(db.DateTime, nullable=True)
    read_at           = db.Column(db.DateTime, nullable=True)

    conversation = db.relationship('Conversation', back_populates='messages')
    sync_ops     = db.relationship('SyncQueue', back_populates='local_message', cascade='all, delete-orphan')

    __table_args__ = (
        Index('idx_conv_sent', 'conversation_id', 'sent_at'),
    )


class SyncQueue(db.Model):
    """PDF: SyncQueue — pending sync ops between client and server."""
    __bind_key__ = 'client'
    __tablename__ = 'SyncQueue'

    sync_id           = db.Column(db.String(191), primary_key=True)
    local_message_id  = db.Column(db.String(191), db.ForeignKey('LocalMessage.local_message_id'), nullable=False)
    operation         = db.Column(db.String(16), nullable=False)   # send | ack | delete
    payload_encrypted = db.Column(db.Text, nullable=True)           # POC: plain payload
    created_at        = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    retry_count       = db.Column(db.Integer, default=0, nullable=False)
    last_error        = db.Column(db.Text, nullable=True)
    status            = db.Column(db.String(16), default='waiting', nullable=False)
    # status: waiting | done | failed

    local_message = db.relationship('LocalMessage', back_populates='sync_ops')


class LocalKeyStore(db.Model):
    """PDF: LocalKeyStore — local crypto keys (identity / session)."""
    __bind_key__ = 'client'
    __tablename__ = 'LocalKeyStore'

    key_id                = db.Column(db.String(191), primary_key=True)
    owner_user_id         = db.Column(db.String(191), nullable=False)
    key_type              = db.Column(db.String(16), nullable=False)   # identity | session
    public_key            = db.Column(db.Text, nullable=True)
    encrypted_private_key = db.Column(db.Text, nullable=True)
    salt                  = db.Column(db.String(191), nullable=True)
    kdf_params_json       = db.Column(db.Text, nullable=True)
    created_at            = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    rotated_at            = db.Column(db.DateTime, nullable=True)
