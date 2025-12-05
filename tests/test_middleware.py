"""
Tests for authentication middleware
"""
import json
import pytest
from datetime import datetime, timedelta
import jwt
import os
from models import db, Token
from utils import hash_token


class TestMiddlewareAuthentication:
    """Tests for middleware JWT validation"""

    def test_middleware_with_valid_access_token(self, authenticated_client, test_user):
        """Test middleware allows request with valid access token"""
        response = authenticated_client.get('/')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['username'] == test_user.Username

    def test_middleware_without_tokens(self, client):
        """Test middleware with no tokens sets current_user to None"""
        response = client.get('/')

        # Should be blocked by @jwt_required decorator
        assert response.status_code in [302, 401]  # Redirect or unauthorized

    def test_middleware_with_invalid_access_token(self, client):
        """Test middleware rejects invalid access token"""
        client.set_cookie('access_token', 'invalid.token.here')

        response = client.get('/')

        # Should be rejected
        assert response.status_code in [302, 401]

    def test_middleware_public_routes(self, client):
        """Test middleware allows public routes without authentication"""
        # Health check should be accessible
        response = client.get('/health')
        assert response.status_code == 200

        # Login page should be accessible
        response = client.get('/auth/login')
        assert response.status_code == 200

        # Register page should be accessible
        response = client.get('/auth/register')
        assert response.status_code == 200


class TestMiddlewareTokenRefresh:
    """Tests for automatic token refresh"""

    def test_middleware_refreshes_expired_access_token(self, client, test_user, expired_access_token, token_record):
        """Test middleware auto-refreshes expired access token"""
        # Set expired access token but valid refresh token
        client.set_cookie('access_token', expired_access_token)
        refresh_token = jwt.encode({
            'user_id': test_user.id,
            'device_id': 'test_device_id',
            'exp': datetime.utcnow() + timedelta(days=90),
            'iat': datetime.utcnow(),
            'type': 'refresh'
        }, os.getenv('JWT_SECRET'), algorithm='HS256')

        # Update token record with correct hash
        token_record.jwt_hash = hash_token(refresh_token)
        db.session.commit()

        client.set_cookie('refresh_token', refresh_token)

        response = client.get('/')

        # Should succeed after refresh
        assert response.status_code == 200

        # Should have new access token in cookies
        cookies = {cookie.name: cookie.value for cookie in client.cookie_jar}
        assert 'access_token' in cookies
        # New token should be different from expired one
        assert cookies['access_token'] != expired_access_token

    def test_middleware_with_expired_refresh_token(self, client, test_user):
        """Test middleware rejects expired refresh token"""
        expired_refresh = jwt.encode({
            'user_id': test_user.id,
            'device_id': 'test_device_id',
            'exp': datetime.utcnow() - timedelta(days=1),  # Expired
            'iat': datetime.utcnow() - timedelta(days=91),
            'type': 'refresh'
        }, os.getenv('JWT_SECRET'), algorithm='HS256')

        client.set_cookie('refresh_token', expired_refresh)

        response = client.get('/')

        # Should be rejected
        assert response.status_code in [302, 401]

    def test_middleware_with_revoked_token(self, client, test_user, auth_tokens):
        """Test middleware rejects revoked refresh token"""
        import uuid

        # Create revoked token record
        token = Token(
            id=str(uuid.uuid4()),
            jwt_hash=hash_token(auth_tokens['refresh_token']),
            id_user=test_user.id,
            device_id='test_device_id',
            device_name='Test Device',
            expired_at=datetime.utcnow() + timedelta(days=90),
            is_revoked=True  # Revoked!
        )
        db.session.add(token)
        db.session.commit()

        client.set_cookie('access_token', auth_tokens['access_token'])
        client.set_cookie('refresh_token', auth_tokens['refresh_token'])

        # Try with expired access token to trigger refresh attempt
        expired_access = jwt.encode({
            'user_id': test_user.id,
            'exp': datetime.utcnow() - timedelta(minutes=1),
            'iat': datetime.utcnow() - timedelta(minutes=11),
            'type': 'access'
        }, os.getenv('JWT_SECRET'), algorithm='HS256')

        client.set_cookie('access_token', expired_access)

        response = client.get('/')

        # Should be rejected because refresh token is revoked
        assert response.status_code in [302, 401]


class TestMiddlewareTokenValidation:
    """Tests for token type validation"""

    def test_middleware_rejects_refresh_token_as_access(self, client, test_user, auth_tokens, token_record):
        """Test middleware rejects refresh token used as access token"""
        # Try to use refresh token as access token
        client.set_cookie('access_token', auth_tokens['refresh_token'])  # Wrong type!
        client.set_cookie('refresh_token', auth_tokens['refresh_token'])

        response = client.get('/')

        # Should be rejected because type is 'refresh', not 'access'
        assert response.status_code in [302, 401]

    def test_middleware_with_token_not_in_database(self, client, test_user):
        """Test middleware rejects token not found in database"""
        # Create valid JWT but don't store in database
        refresh_token = jwt.encode({
            'user_id': test_user.id,
            'device_id': 'unknown_device',
            'exp': datetime.utcnow() + timedelta(days=90),
            'iat': datetime.utcnow(),
            'type': 'refresh'
        }, os.getenv('JWT_SECRET'), algorithm='HS256')

        expired_access = jwt.encode({
            'user_id': test_user.id,
            'exp': datetime.utcnow() - timedelta(minutes=1),
            'iat': datetime.utcnow() - timedelta(minutes=11),
            'type': 'access'
        }, os.getenv('JWT_SECRET'), algorithm='HS256')

        client.set_cookie('access_token', expired_access)
        client.set_cookie('refresh_token', refresh_token)

        response = client.get('/')

        # Should be rejected (token not in database)
        assert response.status_code in [302, 401]


class TestMiddlewareUserLoading:
    """Tests for user loading in middleware"""

    def test_middleware_loads_correct_user(self, authenticated_client, test_user):
        """Test middleware loads the correct user"""
        response = authenticated_client.get('/')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['user']['id'] == test_user.id
        assert data['username'] == test_user.Username

    def test_middleware_updates_last_used(self, authenticated_client, test_user, token_record):
        """Test middleware updates token last_used timestamp"""
        # Get initial last_used
        initial_last_used = token_record.last_used

        # Make request with expired access to trigger refresh
        expired_access = jwt.encode({
            'user_id': test_user.id,
            'exp': datetime.utcnow() - timedelta(minutes=1),
            'iat': datetime.utcnow() - timedelta(minutes=11),
            'type': 'access'
        }, os.getenv('JWT_SECRET'), algorithm='HS256')

        authenticated_client.set_cookie('access_token', expired_access)

        response = authenticated_client.get('/')

        # Refresh token record from database
        db.session.refresh(token_record)

        # last_used should be updated
        if initial_last_used:
            assert token_record.last_used > initial_last_used
        else:
            assert token_record.last_used is not None


class TestMiddlewareHelperFunctions:
    """Tests for middleware helper functions"""

    def test_get_token_record_with_valid_token(self, app, test_user, auth_tokens, token_record):
        """Test get_token_record helper function"""
        from middleware import get_token_record

        with app.app_context():
            result = get_token_record(auth_tokens['refresh_token'])

            assert result is not None
            assert result.id == token_record.id
            assert result.id_user == test_user.id

    def test_get_token_record_with_none(self, app):
        """Test get_token_record with None token"""
        from middleware import get_token_record

        with app.app_context():
            result = get_token_record(None)

            assert result is None

    def test_get_token_record_with_invalid_token(self, app):
        """Test get_token_record with token not in database"""
        from middleware import get_token_record

        with app.app_context():
            result = get_token_record('invalid_token')

            assert result is None
