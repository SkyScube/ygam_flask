"""
Pytest configuration and shared fixtures
"""
import os
import sys
import pytest
from datetime import datetime, timedelta
import jwt

# Add parent directories to path BEFORE any local imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Set test environment before importing app
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['JWT_SECRET'] = 'test_secret_key_for_testing_only_32chars'
os.environ['FLASK_ENV'] = 'testing'

# Now we can import local modules
from src.models import db, User, Role, Token, Message, Log
from src.utils import generate_cuid


@pytest.fixture(scope='function')
def app():
    """Create and configure a test Flask application instance."""
    from src import create_app

    # Override config before creating app
    os.environ['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    os.environ['TESTING'] = 'True'

    # Create app without tables (we'll create them manually for test isolation)
    flask_app = create_app(create_tables=False)

    flask_app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test_secret_key'
    })

    with flask_app.app_context():
        # create_app() already calls db.create_all()
        # But we drop first for clean state in tests
        try:
            db.drop_all()
        except:
            pass  # If tables don't exist yet
        db.create_all()

        # Create default roles
        admin_role = Role(id='role_admin', Name='admin')
        user_role = Role(id='role_user', Name='user')
        db.session.add(admin_role)
        db.session.add(user_role)
        db.session.commit()

        yield flask_app

        db.session.remove()
        db.drop_all()


@pytest.fixture(scope='function')
def client(app):
    """Test client for making requests."""
    return app.test_client()


@pytest.fixture(scope='function')
def runner(app):
    """Test CLI runner."""
    return app.test_cli_runner()


@pytest.fixture
def test_user(app):
    """Create a test user."""
    from models import ph

    user = User(
        id=generate_cuid(),
        Username='testuser',
        Email='test@example.com',
        Password=ph.hash('test_password_hash'),  # Pre-hashed by client
        Is_verified=True,
        Is_activaded=True,
        Id_role='role_user',
        Last_conection=datetime.utcnow()
    )
    db.session.add(user)
    db.session.commit()

    return user


@pytest.fixture
def test_user_2(app):
    """Create a second test user for messaging tests."""
    from models import ph

    user = User(
        id=generate_cuid(),
        Username='testuser2',
        Email='test2@example.com',
        Password=ph.hash('test_password_hash_2'),
        Is_verified=True,
        Is_activaded=True,
        Id_role='role_user',
        Last_conection=datetime.utcnow()
    )
    db.session.add(user)
    db.session.commit()

    return user


@pytest.fixture
def auth_tokens(test_user):
    """Generate valid JWT tokens for test user."""
    access_payload = {
        'user_id': test_user.id,
        'exp': datetime.utcnow() + timedelta(minutes=10),
        'iat': datetime.utcnow(),
        'type': 'access'
    }
    access_token = jwt.encode(access_payload, os.getenv('JWT_SECRET'), algorithm='HS256')

    refresh_payload = {
        'user_id': test_user.id,
        'device_id': 'test_device_id',
        'exp': datetime.utcnow() + timedelta(days=90),
        'iat': datetime.utcnow(),
        'type': 'refresh'
    }
    refresh_token = jwt.encode(refresh_payload, os.getenv('JWT_SECRET'), algorithm='HS256')

    return {
        'access_token': access_token,
        'refresh_token': refresh_token
    }


@pytest.fixture
def expired_access_token(test_user):
    """Generate an expired access token."""
    payload = {
        'user_id': test_user.id,
        'exp': datetime.utcnow() - timedelta(minutes=10),  # Expired 10 min ago
        'iat': datetime.utcnow() - timedelta(minutes=20),
        'type': 'access'
    }
    return jwt.encode(payload, os.getenv('JWT_SECRET'), algorithm='HS256')


@pytest.fixture
def token_record(test_user, auth_tokens):
    """Create a token record in database."""
    from utils import hash_token
    import uuid

    token = Token(
        id=str(uuid.uuid4()),
        jwt_hash=hash_token(auth_tokens['refresh_token']),
        id_user=test_user.id,
        device_id='test_device_id',
        device_name='Test Device',
        expired_at=datetime.utcnow() + timedelta(days=90),
        is_revoked=False
    )
    db.session.add(token)
    db.session.commit()

    return token


@pytest.fixture
def authenticated_client(client, test_user, auth_tokens, token_record):
    """Client with authentication cookies set."""
    client.set_cookie('access_token', auth_tokens['access_token'])
    client.set_cookie('refresh_token', auth_tokens['refresh_token'])
    return client
