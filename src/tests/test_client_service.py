"""Tests for client-side SQLite simulation service."""
import pytest
from datetime import datetime
from src.models import db
from src.client_models import Contact, Conversation, LocalMessage
from src.services.chat_service import persist_message


class TestStoreOutgoing:
    def test_persist_creates_local_message(self, app, test_user, test_user_2):
        persist_message(test_user.id, test_user_2.id, 'hello sqlite')

        msg = LocalMessage.query.filter_by(direction='outgoing').first()
        assert msg is not None
        assert msg.encrypted_content == 'hello sqlite'
        assert msg.status == 'sent'

    def test_persist_creates_contact_for_sender(self, app, test_user, test_user_2):
        persist_message(test_user.id, test_user_2.id, 'hi')

        contact = Contact.query.filter_by(
            owner_user_id=test_user.id,
            server_user_id=test_user_2.id,
        ).first()
        assert contact is not None
        assert contact.username == test_user_2.Username

    def test_persist_creates_conversation_for_sender(self, app, test_user, test_user_2):
        persist_message(test_user.id, test_user_2.id, 'hi')

        contact = Contact.query.filter_by(owner_user_id=test_user.id).first()
        conv = Conversation.query.filter_by(contact_id=contact.contact_id).first()
        assert conv is not None
        assert conv.last_message_preview_encrypted == 'hi'

    def test_outgoing_server_message_id_linked(self, app, test_user, test_user_2):
        result = persist_message(test_user.id, test_user_2.id, 'link test')

        local_msg = LocalMessage.query.filter_by(
            server_message_id=result['id'],
            direction='outgoing',
        ).first()
        assert local_msg is not None


class TestStoreIncoming:
    def test_persist_creates_incoming_for_receiver(self, app, test_user, test_user_2):
        persist_message(test_user.id, test_user_2.id, 'incoming test')

        msg = LocalMessage.query.filter_by(direction='incoming').first()
        assert msg is not None
        assert msg.encrypted_content == 'incoming test'
        assert msg.status == 'received'
        assert msg.received_at is not None

    def test_persist_creates_contact_for_receiver(self, app, test_user, test_user_2):
        persist_message(test_user.id, test_user_2.id, 'hi')

        contact = Contact.query.filter_by(
            owner_user_id=test_user_2.id,
            server_user_id=test_user.id,
        ).first()
        assert contact is not None
        assert contact.username == test_user.Username

    def test_unread_count_increments(self, app, test_user, test_user_2):
        persist_message(test_user.id, test_user_2.id, 'msg1')
        persist_message(test_user.id, test_user_2.id, 'msg2')

        contact = Contact.query.filter_by(
            owner_user_id=test_user_2.id,
            server_user_id=test_user.id,
        ).first()
        conv = Conversation.query.filter_by(contact_id=contact.contact_id).first()
        assert conv.unread_count == 2


class TestIdempotentContactConversation:
    def test_multiple_messages_reuse_same_contact(self, app, test_user, test_user_2):
        persist_message(test_user.id, test_user_2.id, 'a')
        persist_message(test_user.id, test_user_2.id, 'b')

        contacts = Contact.query.filter_by(
            owner_user_id=test_user.id,
            server_user_id=test_user_2.id,
        ).all()
        assert len(contacts) == 1

    def test_multiple_messages_reuse_same_conversation(self, app, test_user, test_user_2):
        persist_message(test_user.id, test_user_2.id, 'a')
        persist_message(test_user.id, test_user_2.id, 'b')

        contact = Contact.query.filter_by(owner_user_id=test_user.id).first()
        convs = Conversation.query.filter_by(contact_id=contact.contact_id).all()
        assert len(convs) == 1

    def test_last_message_preview_updated(self, app, test_user, test_user_2):
        persist_message(test_user.id, test_user_2.id, 'first')
        persist_message(test_user.id, test_user_2.id, 'second')

        contact = Contact.query.filter_by(owner_user_id=test_user.id).first()
        conv = Conversation.query.filter_by(contact_id=contact.contact_id).first()
        assert conv.last_message_preview_encrypted == 'second'

    def test_each_message_creates_local_message(self, app, test_user, test_user_2):
        persist_message(test_user.id, test_user_2.id, 'a')
        persist_message(test_user.id, test_user_2.id, 'b')

        outgoing = LocalMessage.query.filter_by(direction='outgoing').all()
        assert len(outgoing) == 2
