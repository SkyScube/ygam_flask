"""Tests for chat service business logic."""
import pytest
from datetime import datetime
from src.models import db, User, Message
from src.services.chat_service import (
    get_conversations,
    get_message_history,
    persist_message,
    mark_delivered,
    deliver_message,
    search_users,
    _serialize_message,
)
from src.utils import generate_cuid


class TestPersistMessage:
    def test_persist_creates_message(self, app, test_user, test_user_2):
        result = persist_message(test_user.id, test_user_2.id, 'hello')
        assert result['content'] == 'hello'
        assert result['sender_id'] == test_user.id
        assert result['receiver_id'] == test_user_2.id
        assert result['is_delivered'] is False

    def test_persist_saves_to_db(self, app, test_user, test_user_2):
        result = persist_message(test_user.id, test_user_2.id, 'test message')
        msg = Message.query.get(result['id'])
        assert msg is not None
        assert msg.Content == 'test message'

    def test_persist_sets_date(self, app, test_user, test_user_2):
        before = datetime.utcnow()
        result = persist_message(test_user.id, test_user_2.id, 'timed')
        msg = Message.query.get(result['id'])
        assert msg.Date >= before

    def test_persist_returns_serialized(self, app, test_user, test_user_2):
        result = persist_message(test_user.id, test_user_2.id, 'hi')
        assert 'id' in result
        assert 'date' in result
        assert 'is_delivered' in result


class TestMarkDelivered:
    def test_deliver_sets_is_delivered(self, app, test_user, test_user_2):
        """After delivery, Is_delivered=True and the row stays in MySQL."""
        result = persist_message(test_user.id, test_user_2.id, 'deliver me')
        deliver_message(result['id'])
        msg = Message.query.get(result['id'])
        assert msg is not None
        assert msg.Is_delivered is True

    def test_deliver_stores_incoming_sqlite(self, app, test_user, test_user_2):
        """Delivery writes the incoming LocalMessage to the receiver's SQLite."""
        from src.client_models import LocalMessage
        result = persist_message(test_user.id, test_user_2.id, 'deliver me')
        deliver_message(result['id'])
        incoming = LocalMessage.query.filter_by(
            server_message_id=result['id'], direction='incoming'
        ).first()
        assert incoming is not None
        assert incoming.status == 'received'

    def test_noop_on_missing_id(self, app):
        deliver_message('nonexistent_id')


class TestGetConversations:
    def test_empty_when_no_messages(self, app, test_user):
        convs = get_conversations(test_user)
        assert convs == []

    def test_returns_contact_after_sent_message(self, app, test_user, test_user_2):
        persist_message(test_user.id, test_user_2.id, 'hey')
        convs = get_conversations(test_user)
        assert len(convs) == 1
        assert convs[0]['contact_id'] == test_user_2.id
        assert convs[0]['contact_username'] == test_user_2.Username

    def test_returns_contact_after_received_message(self, app, test_user, test_user_2):
        # test_user receives a message only after deliver_message is called
        result = persist_message(test_user_2.id, test_user.id, 'hey back')
        deliver_message(result['id'])
        convs = get_conversations(test_user)
        assert len(convs) == 1
        assert convs[0]['contact_id'] == test_user_2.id

    def test_last_message_is_most_recent(self, app, test_user, test_user_2):
        persist_message(test_user.id, test_user_2.id, 'first')
        persist_message(test_user.id, test_user_2.id, 'second')
        convs = get_conversations(test_user)
        assert convs[0]['last_message'] == 'second'

    def test_deduplicates_conversation(self, app, test_user, test_user_2):
        persist_message(test_user.id, test_user_2.id, 'a')
        result = persist_message(test_user_2.id, test_user.id, 'b')
        deliver_message(result['id'])  # creates incoming side for test_user
        convs = get_conversations(test_user)
        assert len(convs) == 1

    def test_sorted_by_date_desc(self, app, test_user, test_user_2):
        from src.utils import generate_cuid
        user3 = User(
            id=generate_cuid(), Username='user3', Email='u3@x.com',
            Password='hash', Is_activaded=True, Id_role='role_user',
        )
        db.session.add(user3)
        db.session.commit()

        persist_message(test_user.id, test_user_2.id, 'older')
        persist_message(test_user.id, user3.id, 'newer')

        convs = get_conversations(test_user)
        assert len(convs) == 2
        assert convs[0]['contact_id'] == user3.id  # most recent first


class TestGetMessageHistory:
    def test_empty_when_no_messages(self, app, test_user, test_user_2):
        history = get_message_history(test_user, test_user_2.id)
        assert history == []

    def test_returns_messages_between_two_users(self, app, test_user, test_user_2):
        # outgoing is stored on persist, incoming only on delivery
        persist_message(test_user.id, test_user_2.id, 'hi')
        result = persist_message(test_user_2.id, test_user.id, 'hello')
        deliver_message(result['id'])
        history = get_message_history(test_user, test_user_2.id)
        assert len(history) == 2

    def test_ordered_ascending(self, app, test_user, test_user_2):
        persist_message(test_user.id, test_user_2.id, 'first')
        persist_message(test_user.id, test_user_2.id, 'second')
        history = get_message_history(test_user, test_user_2.id)
        assert history[0]['content'] == 'first'
        assert history[1]['content'] == 'second'

    def test_limit_is_respected(self, app, test_user, test_user_2):
        for i in range(5):
            persist_message(test_user.id, test_user_2.id, f'msg {i}')
        history = get_message_history(test_user, test_user_2.id, limit=3)
        assert len(history) == 3

    def test_isolation_from_third_party(self, app, test_user, test_user_2):
        user3 = User(
            id=generate_cuid(), Username='user3b', Email='u3b@x.com',
            Password='hash', Is_activaded=True, Id_role='role_user',
        )
        db.session.add(user3)
        db.session.commit()

        persist_message(test_user.id, test_user_2.id, 'private')
        persist_message(test_user.id, user3.id, 'other conversation')

        history = get_message_history(test_user, test_user_2.id)
        assert len(history) == 1
        assert history[0]['content'] == 'private'


class TestSearchUsers:
    def test_finds_by_prefix(self, app, test_user, test_user_2):
        results = search_users('testuser', test_user.id)
        usernames = [u.Username for u in results]
        assert test_user_2.Username in usernames

    def test_excludes_self(self, app, test_user):
        results = search_users('test', test_user.id)
        ids = [u.id for u in results]
        assert test_user.id not in ids

    def test_no_match_returns_empty(self, app, test_user):
        results = search_users('zzznomatch', test_user.id)
        assert results == []

    def test_prefix_only(self, app, test_user, test_user_2):
        # 'user2' is a suffix, not a prefix of 'testuser2' starting from 'user'
        # 'testuser2' starts with 'test', so prefix 'testuser2' should match
        results = search_users('testuser2', test_user.id)
        assert any(u.Username == 'testuser2' for u in results)

    def test_limit_respected(self, app, test_user):
        for i in range(5):
            u = User(
                id=generate_cuid(), Username=f'alpha{i}', Email=f'alpha{i}@x.com',
                Password='hash', Is_activaded=True, Id_role='role_user',
            )
            db.session.add(u)
        db.session.commit()
        results = search_users('alpha', test_user.id, limit=3)
        assert len(results) <= 3


class TestSerializeMessage:
    def test_fields_present(self, app, test_user, test_user_2):
        result = persist_message(test_user.id, test_user_2.id, 'serialize me')
        assert set(result.keys()) == {'id', 'sender_id', 'receiver_id', 'content', 'date', 'is_delivered'}
