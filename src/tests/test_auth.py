"""
Tests for authentication routes
"""
import json
import pytest
from src.models import db, User, Token
from src.utils import hash_token


class TestRegister:
    """Tests for POST /api/auth/register"""

    def test_register_success(self, client):
        """Test successful user registration"""
        response = client.post('/api/auth/register',
                                json={
                                    'username': 'newuser',
                                    'email': 'newuser@example.com',
                                    'password': 'hashed_password'
                                })

        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['message'] == 'Compte créé avec succès'

        # Verify user exists in database
        user = User.query.filter_by(Email='newuser@example.com').first()
        assert user is not None
        assert user.Username == 'newuser'
        assert user.Is_activaded is True
        assert user.Id_role == 'user'

    def test_register_duplicate_email(self, client, test_user):
        """Test registration with existing email"""
        response = client.post('/api/auth/register',
                                json={
                                    'username': 'anotheruser',
                                    'email': test_user.Email,  # Duplicate
                                    'password': 'hashed_password'
                                })

        assert response.status_code == 409

    def test_register_duplicate_username(self, client, test_user):
        """Test registration with existing username"""
        response = client.post('/api/auth/register',
                                json={
                                    'username': test_user.Username,  # Duplicate
                                    'email': 'different@example.com',
                                    'password': 'hashed_password'
                                })

        assert response.status_code == 409

    def test_register_missing_fields(self, client):
        """Test registration with missing required fields"""
        response = client.post('/api/auth/register',
                                json={
                                    'username': 'newuser'
                                    # Missing email and password
                                })

        assert response.status_code == 400


class TestLogin:
    """Tests for POST /api/auth/login"""

    def test_login_success(self, client, test_user):
        """Test successful login"""
        response = client.post('/api/auth/login',
                                json={
                                    'identifier': test_user.Email,
                                    'password': 'test_password_hash',
                                    'remember': False
                                })

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['message'] == 'Connexion réussie'
        assert data['user']['id'] == test_user.id
        assert data['user']['username'] == test_user.Username
        assert data['user']['email'] == test_user.Email

        # Check cookies are set (Flask test client stores cookies differently)
        # Cookies are automatically stored in the client session

        # Verify token record in database
        token = Token.query.filter_by(id_user=test_user.id).first()
        assert token is not None
        assert token.is_revoked is False

    def test_login_by_username(self, client, test_user):
        """Test login using username instead of email"""
        response = client.post('/api/auth/login',
                                json={
                                    'identifier': test_user.Username,
                                    'password': 'test_password_hash',
                                    'remember': False
                                })

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['message'] == 'Connexion réussie'
        assert data['user']['username'] == test_user.Username

    def test_login_wrong_password(self, client, test_user):
        """Test login with incorrect password"""
        response = client.post('/api/auth/login',
                                json={
                                    'identifier': test_user.Email,
                                    'password': 'wrong_password',
                                    'remember': False
                                })

        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['message'] == 'Email ou mot de passe incorrect'

    def test_login_nonexistent_user(self, client):
        """Test login with non-existent email"""
        response = client.post('/api/auth/login',
                                json={
                                    'identifier': 'nonexistent@example.com',
                                    'password': 'any_password',
                                    'remember': False
                                })

        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['message'] == 'Email ou mot de passe incorrect'

    def test_login_missing_fields(self, client):
        """Test login with missing fields"""
        response = client.post('/api/auth/login',
                                json={
                                    'identifier': 'test@example.com'
                                    # Missing password
                                })

        # Should handle gracefully
        assert response.status_code in [400, 401, 500]


class TestLogout:
    """Tests for POST /api/auth/logout"""

    def test_logout_success(self, authenticated_client, test_user, token_record):
        """Test successful logout"""
        response = authenticated_client.post('/api/auth/logout')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['message'] == 'Déconnexion réussie'

        # Verify token is revoked in database
        db.session.refresh(token_record)
        assert token_record.is_revoked is True

        # Cookies are cleared by setting max_age=0 in the response

    def test_logout_without_auth(self, client):
        """Test logout without authentication"""
        response = client.post('/api/auth/logout')

        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['message'] == 'Non authentifié'

    def test_logout_with_invalid_token(self, client):
        """Test logout with invalid token"""
        client.set_cookie('access_token', 'invalid.token.here')
        client.set_cookie('refresh_token', 'invalid.token.here')

        response = client.post('/api/auth/logout')

        # Middleware should reject and set current_user to None
        assert response.status_code == 401


class TestAuthViews:
    """Tests for HTML auth views"""

    def test_register_view(self, client):
        """Test GET /auth/register returns HTML"""
        response = client.get('/auth/register')

        assert response.status_code == 200
        assert b'<!DOCTYPE html>' in response.data or b'<html' in response.data

    def test_login_view(self, client):
        """Test GET /auth/login returns HTML"""
        response = client.get('/auth/login')

        assert response.status_code == 200
        assert b'<!DOCTYPE html>' in response.data or b'<html' in response.data


class TestTokenManagement:
    """Tests for token creation and management"""

    def test_token_stored_as_hash(self, client, test_user):
        """Test that refresh token is stored as hash, not plaintext"""
        response = client.post('/api/auth/login',
                                json={
                                    'identifier': test_user.Email,
                                    'password': 'test_password_hash',
                                    'remember': False
                                })

        assert response.status_code == 200

        # Get the refresh token from response set_cookie calls
        # In test environment, we can get it from the token record
        refresh_token = Token.query.filter_by(id_user=test_user.id).first()

        # Verify token exists in database
        token = Token.query.filter_by(id_user=test_user.id).first()
        assert token is not None
        assert token.jwt_hash is not None
        # Token hash should be 64 characters (SHA256)
        assert len(token.jwt_hash) == 64

    def test_token_device_tracking(self, client, test_user):
        """Test that tokens track device information"""
        response = client.post('/api/auth/login',
                                json={
                                    'identifier': test_user.Email,
                                    'password': 'test_password_hash',
                                    'remember': False,
                                    'device_name': 'Test Browser'
                                })

        assert response.status_code == 200

        token = Token.query.filter_by(id_user=test_user.id).first()
        assert token.device_name == 'Test Browser'
        assert token.device_id is not None

    def test_multiple_device_tokens(self, client, test_user):
        """Test that user can have multiple tokens for different devices"""
        # Login from device 1
        response1 = client.post('/api/auth/login',
                                 json={
                                     'identifier': test_user.Email,
                                     'password': 'test_password_hash',
                                     'device_name': 'Device 1'
                                 })
        assert response1.status_code == 200

        # Login from device 2 (simulate new session)
        client2 = client.application.test_client()
        response2 = client2.post('/api/auth/login',
                                  json={
                                      'identifier': test_user.Email,
                                      'password': 'test_password_hash',
                                      'device_name': 'Device 2'
                                  })
        assert response2.status_code == 200

        # Both tokens should exist
        tokens = Token.query.filter_by(id_user=test_user.id).all()
        assert len(tokens) == 2
        assert tokens[0].device_id != tokens[1].device_id
