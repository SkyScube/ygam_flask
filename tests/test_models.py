"""
Tests for database models
"""
import pytest
from datetime import datetime, timedelta
from models import db, User, Role, Message, Token, Log, ph
from utils import generate_cuid
import uuid


class TestUserModel:
    """Tests for User model"""

    def test_create_user(self, app):
        """Test creating a user"""
        user = User(
            id=generate_cuid(),
            Username='testuser',
            Email='test@example.com',
            Password=ph.hash('password'),
            Is_verified=False,
            Is_activaded=True,
            Id_role='role_user'
        )
        db.session.add(user)
        db.session.commit()

        assert user.id is not None
        assert user.Username == 'testuser'
        assert user.Email == 'test@example.com'

    def test_user_unique_email(self, app, test_user):
        """Test email uniqueness constraint"""
        duplicate_user = User(
            id=generate_cuid(),
            Username='different',
            Email=test_user.Email,  # Duplicate
            Password=ph.hash('password'),
            Id_role='role_user'
        )
        db.session.add(duplicate_user)

        with pytest.raises(Exception):  # IntegrityError
            db.session.commit()

    def test_user_unique_username(self, app, test_user):
        """Test username uniqueness constraint"""
        duplicate_user = User(
            id=generate_cuid(),
            Username=test_user.Username,  # Duplicate
            Email='different@example.com',
            Password=ph.hash('password'),
            Id_role='role_user'
        )
        db.session.add(duplicate_user)

        with pytest.raises(Exception):  # IntegrityError
            db.session.commit()

    def test_user_set_password(self, app):
        """Test set_password method"""
        user = User(
            id=generate_cuid(),
            Username='testuser',
            Email='test@example.com',
            Password='temp',
            Id_role='role_user'
        )

        user.set_password('my_secure_password')

        assert user.Password != 'my_secure_password'  # Should be hashed
        assert ph.verify(user.Password, 'my_secure_password')  # Should verify

    def test_user_role_relationship(self, app):
        """Test user-role relationship"""
        role = Role.query.filter_by(Name='user').first()
        user = User(
            id=generate_cuid(),
            Username='testuser',
            Email='test@example.com',
            Password=ph.hash('password'),
            Id_role=role.id
        )
        db.session.add(user)
        db.session.commit()

        assert user.role is not None
        assert user.role.Name == 'user'

    def test_user_tokens_relationship(self, app, test_user, token_record):
        """Test user-tokens relationship"""
        assert len(test_user.tokens) > 0
        assert test_user.tokens[0].id_user == test_user.id

    def test_user_cascade_delete_tokens(self, app, test_user, token_record):
        """Test that deleting user cascades to tokens"""
        user_id = test_user.id
        token_id = token_record.id

        db.session.delete(test_user)
        db.session.commit()

        # Token should be deleted (cascade)
        assert Token.query.get(token_id) is None


class TestRoleModel:
    """Tests for Role model"""

    def test_create_role(self, app):
        """Test creating a role"""
        role = Role(
            id='role_moderator',
            Name='moderator'
        )
        db.session.add(role)
        db.session.commit()

        assert role.id == 'role_moderator'
        assert role.Name == 'moderator'

    def test_role_users_relationship(self, app, test_user):
        """Test role-users relationship"""
        role = Role.query.get(test_user.Id_role)

        assert len(role.users) > 0
        assert test_user in role.users


class TestMessageModel:
    """Tests for Message model"""

    def test_create_message(self, app, test_user, test_user_2):
        """Test creating a message"""
        message = Message(
            id=generate_cuid(),
            Id_user_sender=test_user.id,
            Id_user_receiver=test_user_2.id,
            Content=b'encrypted_content_here',
            Is_delivered=False,
            Date=datetime.utcnow()
        )
        db.session.add(message)
        db.session.commit()

        assert message.id is not None
        assert message.Id_user_sender == test_user.id
        assert message.Id_user_receiver == test_user_2.id
        assert message.Is_delivered is False

    def test_message_sender_relationship(self, app, test_user, test_user_2):
        """Test message sender relationship"""
        message = Message(
            id=generate_cuid(),
            Id_user_sender=test_user.id,
            Id_user_receiver=test_user_2.id,
            Content=b'encrypted',
            Is_delivered=False
        )
        db.session.add(message)
        db.session.commit()

        assert message.sender.id == test_user.id
        assert message.sender.Username == test_user.Username

    def test_message_receiver_relationship(self, app, test_user, test_user_2):
        """Test message receiver relationship"""
        message = Message(
            id=generate_cuid(),
            Id_user_sender=test_user.id,
            Id_user_receiver=test_user_2.id,
            Content=b'encrypted',
            Is_delivered=False
        )
        db.session.add(message)
        db.session.commit()

        assert message.receiver.id == test_user_2.id
        assert message.receiver.Username == test_user_2.Username

    def test_message_content_binary(self, app, test_user, test_user_2):
        """Test message can store binary content"""
        binary_content = b'\x00\x01\x02\x03\xff\xfe'
        message = Message(
            id=generate_cuid(),
            Id_user_sender=test_user.id,
            Id_user_receiver=test_user_2.id,
            Content=binary_content,
            Is_delivered=False
        )
        db.session.add(message)
        db.session.commit()

        retrieved = Message.query.get(message.id)
        assert retrieved.Content == binary_content

    def test_user_sent_messages(self, app, test_user, test_user_2):
        """Test user sent_messages relationship"""
        message = Message(
            id=generate_cuid(),
            Id_user_sender=test_user.id,
            Id_user_receiver=test_user_2.id,
            Content=b'encrypted',
            Is_delivered=False
        )
        db.session.add(message)
        db.session.commit()

        sent_messages = list(test_user.sent_messages)
        assert len(sent_messages) == 1
        assert sent_messages[0].id == message.id

    def test_user_received_messages(self, app, test_user, test_user_2):
        """Test user received_messages relationship"""
        message = Message(
            id=generate_cuid(),
            Id_user_sender=test_user.id,
            Id_user_receiver=test_user_2.id,
            Content=b'encrypted',
            Is_delivered=False
        )
        db.session.add(message)
        db.session.commit()

        received_messages = list(test_user_2.received_messages)
        assert len(received_messages) == 1
        assert received_messages[0].id == message.id


class TestTokenModel:
    """Tests for Token model"""

    def test_create_token(self, app, test_user):
        """Test creating a token"""
        token = Token(
            id=str(uuid.uuid4()),
            jwt_hash='hash_of_jwt_token',
            id_user=test_user.id,
            device_id='device_123',
            device_name='Chrome Browser',
            expired_at=datetime.utcnow() + timedelta(days=90),
            is_revoked=False
        )
        db.session.add(token)
        db.session.commit()

        assert token.id is not None
        assert token.is_revoked is False
        assert token.creation_date is not None

    def test_token_user_relationship(self, app, test_user, token_record):
        """Test token-user relationship"""
        assert token_record.user.id == test_user.id
        assert token_record.user.Username == test_user.Username

    def test_token_unique_jwt_hash(self, app, test_user):
        """Test jwt_hash uniqueness constraint"""
        token1 = Token(
            id=str(uuid.uuid4()),
            jwt_hash='same_hash',
            id_user=test_user.id,
            device_id='device_1',
            expired_at=datetime.utcnow() + timedelta(days=90)
        )
        db.session.add(token1)
        db.session.commit()

        token2 = Token(
            id=str(uuid.uuid4()),
            jwt_hash='same_hash',  # Duplicate
            id_user=test_user.id,
            device_id='device_2',
            expired_at=datetime.utcnow() + timedelta(days=90)
        )
        db.session.add(token2)

        with pytest.raises(Exception):  # IntegrityError
            db.session.commit()

    def test_token_unique_device_id(self, app, test_user):
        """Test device_id uniqueness constraint"""
        token1 = Token(
            id=str(uuid.uuid4()),
            jwt_hash='hash_1',
            id_user=test_user.id,
            device_id='same_device',
            expired_at=datetime.utcnow() + timedelta(days=90)
        )
        db.session.add(token1)
        db.session.commit()

        token2 = Token(
            id=str(uuid.uuid4()),
            jwt_hash='hash_2',
            id_user=test_user.id,
            device_id='same_device',  # Duplicate
            expired_at=datetime.utcnow() + timedelta(days=90)
        )
        db.session.add(token2)

        with pytest.raises(Exception):  # IntegrityError
            db.session.commit()

    def test_token_default_values(self, app, test_user):
        """Test token default values"""
        token = Token(
            id=str(uuid.uuid4()),
            jwt_hash='hash',
            id_user=test_user.id,
            device_id='device',
            expired_at=datetime.utcnow() + timedelta(days=90)
        )
        db.session.add(token)
        db.session.commit()

        assert token.is_revoked is False
        assert token.creation_date is not None
        assert isinstance(token.creation_date, datetime)


class TestLogModel:
    """Tests for Log model"""

    def test_create_log(self, app, test_user):
        """Test creating a log entry"""
        log = Log(
            id=generate_cuid(),
            action='CREATE',
            target_table='User',
            target_id=test_user.id,
            actor_user_id=test_user.id,
            date=datetime.utcnow()
        )
        db.session.add(log)
        db.session.commit()

        assert log.id is not None
        assert log.action == 'CREATE'
        assert log.date is not None

    def test_log_default_date(self, app, test_user):
        """Test log default date"""
        log = Log(
            id=generate_cuid(),
            action='READ',
            target_table='Message',
            target_id='msg_123',
            actor_user_id=test_user.id
        )
        db.session.add(log)
        db.session.commit()

        assert log.date is not None
        assert isinstance(log.date, datetime)

    def test_log_action_types(self, app, test_user):
        """Test different log action types"""
        actions = ['CREATE', 'READ', 'UPDATE', 'DELETE']

        for action in actions:
            log = Log(
                id=generate_cuid(),
                action=action,
                target_table='User',
                target_id=test_user.id,
                actor_user_id=test_user.id
            )
            db.session.add(log)

        db.session.commit()

        logs = Log.query.filter_by(actor_user_id=test_user.id).all()
        assert len(logs) == 4
        log_actions = [log.action for log in logs]
        assert set(log_actions) == set(actions)
