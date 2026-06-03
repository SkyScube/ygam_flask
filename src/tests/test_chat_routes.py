"""Tests for chat REST API routes."""
import json
import pytest
from src.models import db, User
from src.services.chat_service import persist_message
from src.utils import generate_cuid


class TestConversationsRoute:
    def test_requires_auth(self, client):
        resp = client.get('/api/conversations')
        assert resp.status_code == 401

    def test_returns_empty_list(self, authenticated_client):
        resp = authenticated_client.get('/api/conversations')
        assert resp.status_code == 200
        assert json.loads(resp.data) == []

    def test_returns_conversations(self, authenticated_client, test_user, test_user_2, app):
        with app.app_context():
            persist_message(test_user.id, test_user_2.id, 'hello')
        resp = authenticated_client.get('/api/conversations')
        data = json.loads(resp.data)
        assert len(data) == 1
        assert data[0]['contact_id'] == test_user_2.id


class TestMessagesRoute:
    def test_requires_auth(self, client, test_user_2):
        resp = client.get(f'/api/messages/{test_user_2.id}')
        assert resp.status_code == 401

    def test_empty_history(self, authenticated_client, test_user_2):
        resp = authenticated_client.get(f'/api/messages/{test_user_2.id}')
        assert resp.status_code == 200
        assert json.loads(resp.data) == []

    def test_returns_messages(self, authenticated_client, test_user, test_user_2, app):
        with app.app_context():
            persist_message(test_user.id, test_user_2.id, 'test msg')
        resp = authenticated_client.get(f'/api/messages/{test_user_2.id}')
        data = json.loads(resp.data)
        assert len(data) == 1
        assert data[0]['content'] == 'test msg'

    def test_isolation(self, authenticated_client, test_user, test_user_2, app):
        user3 = None
        with app.app_context():
            user3 = User(
                id=generate_cuid(), Username='user3c', Email='u3c@x.com',
                Password='hash', Is_activaded=True, Id_role='role_user',
            )
            db.session.add(user3)
            db.session.commit()
            user3_id = user3.id
            persist_message(test_user.id, test_user_2.id, 'private')
            persist_message(test_user.id, user3_id, 'other')

        resp = authenticated_client.get(f'/api/messages/{test_user_2.id}')
        data = json.loads(resp.data)
        assert len(data) == 1
        assert data[0]['content'] == 'private'


class TestSearchUsersRoute:
    def test_requires_auth(self, client):
        resp = client.get('/api/users/search?q=test')
        assert resp.status_code == 401

    def test_short_query_returns_empty(self, authenticated_client):
        resp = authenticated_client.get('/api/users/search?q=a')
        assert resp.status_code == 200
        assert json.loads(resp.data) == []

    def test_missing_query_returns_empty(self, authenticated_client):
        resp = authenticated_client.get('/api/users/search')
        assert resp.status_code == 200
        assert json.loads(resp.data) == []

    def test_finds_user(self, authenticated_client, test_user_2):
        resp = authenticated_client.get('/api/users/search?q=testuser2')
        data = json.loads(resp.data)
        assert any(u['username'] == 'testuser2' for u in data)

    def test_excludes_self(self, authenticated_client, test_user):
        resp = authenticated_client.get('/api/users/search?q=testuser')
        data = json.loads(resp.data)
        assert not any(u['id'] == test_user.id for u in data)

    def test_response_shape(self, authenticated_client, test_user_2):
        resp = authenticated_client.get('/api/users/search?q=testuser2')
        data = json.loads(resp.data)
        if data:
            assert 'id' in data[0]
            assert 'username' in data[0]


class TestChatPage:
    def test_requires_auth(self, client):
        resp = client.get('/chat')
        # Should redirect to login (302) or return 401
        assert resp.status_code in (302, 401)

    def test_authenticated_returns_html(self, authenticated_client):
        resp = authenticated_client.get('/chat')
        assert resp.status_code == 200
        assert b'<html' in resp.data or b'<!DOCTYPE' in resp.data
