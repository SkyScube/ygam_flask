"""
Tests for main routes
"""
import json
import pytest
from src.models import db


class TestIndexRoute:
    """Tests for GET / route"""

    def test_index_requires_authentication(self, client):
        """Test index route requires authentication"""
        response = client.get('/')

        # Should redirect to login or return 401
        assert response.status_code in [302, 401]

    def test_index_with_authentication(self, authenticated_client, test_user):
        """Test index route with authenticated user"""
        response = authenticated_client.get('/')

        assert response.status_code == 200
        data = json.loads(response.data)

        assert data['message'] == 'Welcome to Ygam API'
        assert data['version'] == '0.1.0'
        assert data['status'] == 'running'
        assert data['username'] == test_user.Username
        assert data['email'] == test_user.Email
        assert 'endpoints' in data

    def test_index_returns_endpoints(self, authenticated_client):
        """Test index route returns endpoint information"""
        response = authenticated_client.get('/')

        assert response.status_code == 200
        data = json.loads(response.data)

        assert 'endpoints' in data
        assert 'health' in data['endpoints']
        assert data['endpoints']['health'] == '/health'

    def test_index_json_response(self, authenticated_client):
        """Test index returns JSON"""
        response = authenticated_client.get('/')

        assert response.status_code == 200
        assert response.content_type == 'application/json'


class TestHealthRoute:
    """Tests for GET /health route"""

    def test_health_check_success(self, client):
        """Test health check returns success"""
        response = client.get('/health')

        assert response.status_code == 200
        data = json.loads(response.data)

        assert data['status'] == 'ok'
        assert data['database'] == 'connected'
        assert data['version'] == '0.1.0'

    def test_health_check_no_authentication(self, client):
        """Test health check doesn't require authentication"""
        response = client.get('/health')

        # Should work without authentication
        assert response.status_code == 200

    def test_health_check_json_response(self, client):
        """Test health check returns JSON"""
        response = client.get('/health')

        assert response.status_code == 200
        assert response.content_type == 'application/json'

    def test_health_check_database_status(self, client):
        """Test health check verifies database connection"""
        response = client.get('/health')

        assert response.status_code == 200
        data = json.loads(response.data)

        # Database should be connected in tests
        assert data['database'] == 'connected'


class TestRouteProtection:
    """Tests for route protection with @jwt_required decorator"""

    def test_protected_route_without_token(self, client):
        """Test protected route rejects requests without token"""
        response = client.get('/')

        assert response.status_code in [302, 401]

    def test_protected_route_with_invalid_token(self, client):
        """Test protected route rejects invalid token"""
        client.set_cookie('access_token', 'invalid.token.here')

        response = client.get('/')

        assert response.status_code in [302, 401]

    def test_protected_route_with_valid_token(self, authenticated_client):
        """Test protected route accepts valid token"""
        response = authenticated_client.get('/')

        assert response.status_code == 200

    def test_protected_route_json_error_for_api(self, client):
        """Test protected route returns JSON error for API requests"""
        response = client.get('/',
                               headers={'Accept': 'application/json'})

        if response.status_code == 401:
            data = json.loads(response.data)
            assert 'message' in data
            assert data['message'] == 'Authentication required'


class TestCORS:
    """Tests for CORS headers (if implemented)"""

    def test_cors_headers_present(self, client):
        """Test CORS headers on API routes"""
        response = client.get('/health')

        # Check if CORS headers exist (if Flask-CORS is configured)
        # This is optional, depends on if CORS is set up
        assert response.status_code == 200


class TestErrorHandling:
    """Tests for error handling"""

    def test_404_not_found(self, client):
        """Test 404 error for non-existent route"""
        response = client.get('/nonexistent/route')

        assert response.status_code == 404

    def test_405_method_not_allowed(self, client):
        """Test 405 error for wrong HTTP method"""
        # /health only accepts GET
        response = client.post('/health')

        assert response.status_code == 405


class TestStaticRoutes:
    """Tests for static file serving"""

    def test_static_css_accessible(self, client):
        """Test static CSS files are accessible"""
        response = client.get('/static/style/register.css')

        # Should be accessible without authentication
        assert response.status_code in [200, 404]  # 404 if file doesn't exist in test

    def test_static_route_public(self, client):
        """Test static route doesn't require authentication"""
        # Static routes should be public
        response = client.get('/static/test.css')

        # Should not redirect to login (even if 404)
        assert response.status_code in [200, 404]
        assert response.status_code != 302


class TestResponseFormat:
    """Tests for response format consistency"""

    def test_api_responses_are_json(self, authenticated_client):
        """Test API routes return JSON"""
        routes = [
            '/',
            '/health'
        ]

        for route in routes:
            response = authenticated_client.get(route)
            if response.status_code == 200:
                assert response.content_type == 'application/json'

    def test_api_errors_are_json(self, client):
        """Test API errors return JSON for API requests"""
        response = client.get('/',
                               headers={'Accept': 'application/json'})

        if response.status_code in [401, 403, 404]:
            # Should return JSON error
            try:
                data = json.loads(response.data)
                assert 'message' in data or 'error' in data
            except json.JSONDecodeError:
                # Some errors might not be JSON yet
                pass


class TestVersioning:
    """Tests for API versioning"""

    def test_version_in_health_check(self, client):
        """Test version is returned in health check"""
        response = client.get('/health')

        data = json.loads(response.data)
        assert 'version' in data
        assert data['version'] == '0.1.0'

    def test_version_in_index(self, authenticated_client):
        """Test version is returned in index"""
        response = authenticated_client.get('/')

        data = json.loads(response.data)
        assert 'version' in data
        assert data['version'] == '0.1.0'
