"""Tests for Socket.IO events."""
import os
import pytest
import jwt
from datetime import datetime, timedelta

from src.models import db, Message
from src.extensions import socketio
from src.sockets.chat import connected_users


def _make_access_token(user_id):
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(minutes=10),
        'iat': datetime.utcnow(),
        'type': 'access'
    }
    return jwt.encode(payload, os.getenv('JWT_SECRET'), algorithm='HS256')


@pytest.fixture
def socket_client(app, test_user):
    """Authenticated socket client for test_user."""
    token = _make_access_token(test_user.id)
    flask_client = app.test_client()
    flask_client.set_cookie('access_token', token)
    sc = socketio.test_client(app, flask_test_client=flask_client)
    yield sc
    if sc.is_connected():
        sc.disconnect()


@pytest.fixture
def socket_client_2(app, test_user_2):
    """Authenticated socket client for test_user_2."""
    token = _make_access_token(test_user_2.id)
    flask_client = app.test_client()
    flask_client.set_cookie('access_token', token)
    sc = socketio.test_client(app, flask_test_client=flask_client)
    yield sc
    if sc.is_connected():
        sc.disconnect()


@pytest.fixture
def unauth_socket_client(app):
    """Unauthenticated socket client."""
    sc = socketio.test_client(app)
    yield sc
    try:
        sc.disconnect()
    except Exception:
        pass


class TestSocketConnect:
    def test_authenticated_user_connects(self, socket_client, test_user):
        assert socket_client.is_connected()

    def test_unauthenticated_user_refused(self, unauth_socket_client):
        assert not unauth_socket_client.is_connected()

    def test_connected_event_received(self, socket_client, test_user):
        received = socket_client.get_received()
        events = [e for e in received if e['name'] == 'connected']
        assert len(events) == 1
        assert events[0]['args'][0]['user_id'] == test_user.id


class TestSocketDisconnect:
    def test_disconnect_removes_from_connected_users(self, app, test_user):
        token = _make_access_token(test_user.id)
        flask_client = app.test_client()
        flask_client.set_cookie('access_token', token)
        sc = socketio.test_client(app, flask_test_client=flask_client)
        assert sc.is_connected()
        sc.disconnect()
        assert not sc.is_connected()


class TestSendMessage:
    def test_send_message_basic(self, app, socket_client, socket_client_2, test_user, test_user_2):
        socket_client.get_received()  # clear connect event
        socket_client_2.get_received()

        socket_client.emit('send_message', {'to': test_user_2.id, 'content': 'hello socket'})

        sent_events = socket_client.get_received()
        recv_events = socket_client_2.get_received()

        sent_names = [e['name'] for e in sent_events]
        recv_names = [e['name'] for e in recv_events]

        assert 'message_sent' in sent_names
        assert 'new_message' in recv_names

    def test_send_message_removed_after_online_delivery(self, app, socket_client, socket_client_2, test_user, test_user_2):
        """When receiver is connected, message is deleted from MySQL after delivery."""
        socket_client.emit('send_message', {'to': test_user_2.id, 'content': 'relay test'})

        with app.app_context():
            # Receiver was online → deliver_message() was called → MySQL row deleted
            msg = Message.query.filter_by(
                Id_user_sender=test_user.id,
                Id_user_receiver=test_user_2.id
            ).first()
            assert msg is None

    def test_send_message_stored_in_sqlite_after_delivery(self, app, socket_client, socket_client_2, test_user, test_user_2):
        """Both sides (outgoing + incoming) must appear in SQLite after delivery."""
        from src.client_models import LocalMessage
        socket_client.emit('send_message', {'to': test_user_2.id, 'content': 'sqlite check'})

        with app.app_context():
            outgoing = LocalMessage.query.filter_by(direction='outgoing').first()
            incoming = LocalMessage.query.filter_by(direction='incoming').first()
            assert outgoing is not None
            assert incoming is not None

    def test_send_message_content(self, app, socket_client, socket_client_2, test_user, test_user_2):
        socket_client.get_received()
        socket_client_2.get_received()

        socket_client.emit('send_message', {'to': test_user_2.id, 'content': 'specific content'})

        recv_events = socket_client_2.get_received()
        new_msg_events = [e for e in recv_events if e['name'] == 'new_message']
        assert len(new_msg_events) >= 1
        assert new_msg_events[0]['args'][0]['content'] == 'specific content'

    def test_send_message_missing_receiver(self, socket_client):
        socket_client.get_received()
        socket_client.emit('send_message', {'content': 'no receiver'})
        events = socket_client.get_received()
        error_events = [e for e in events if e['name'] == 'error']
        assert len(error_events) == 1

    def test_send_message_missing_content(self, socket_client, test_user_2):
        socket_client.get_received()
        socket_client.emit('send_message', {'to': test_user_2.id, 'content': ''})
        events = socket_client.get_received()
        error_events = [e for e in events if e['name'] == 'error']
        assert len(error_events) == 1

    def test_send_message_nonexistent_receiver(self, socket_client):
        socket_client.get_received()
        socket_client.emit('send_message', {'to': 'nonexistent_user_id', 'content': 'hi'})
        events = socket_client.get_received()
        error_events = [e for e in events if e['name'] == 'error']
        assert len(error_events) == 1

    def test_message_not_delivered_to_sender_room(self, app, socket_client, socket_client_2, test_user, test_user_2):
        """Sender should get message_sent, not new_message."""
        socket_client.get_received()
        socket_client_2.get_received()

        socket_client.emit('send_message', {'to': test_user_2.id, 'content': 'routing test'})

        sent_events = socket_client.get_received()
        sent_names = {e['name'] for e in sent_events}
        assert 'message_sent' in sent_names
        # Sender should NOT receive new_message (that's for the receiver)
        assert 'new_message' not in sent_names

    def test_conversation_isolation(self, app, socket_client, socket_client_2, test_user, test_user_2):
        """Messages sent to user2 are only received by user2."""
        socket_client_2.get_received()
        socket_client.emit('send_message', {'to': test_user_2.id, 'content': 'private'})
        recv = socket_client_2.get_received()
        msg_events = [e for e in recv if e['name'] == 'new_message']
        assert len(msg_events) == 1
        assert msg_events[0]['args'][0]['receiver_id'] == test_user_2.id
