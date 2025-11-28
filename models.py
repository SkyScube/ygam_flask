from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import Index
from argon2 import PasswordHasher

db = SQLAlchemy()
ph = PasswordHasher()


class User(db.Model):
    __tablename__ = 'User'

    id = db.Column(db.String(191), primary_key=True)
    Username = db.Column(db.String(191), unique=True, nullable=False)
    Email = db.Column(db.String(191), unique=True, nullable=False)
    Password = db.Column(db.String(128), nullable=False)
    Is_verified = db.Column(db.Boolean, default=False, nullable=False)
    Is_activaded = db.Column(db.Boolean, default=False, nullable=False)
    Last_conection = db.Column(db.DateTime, nullable=True)

    # Foreign Key vers Role
    Id_role = db.Column(db.String(191), db.ForeignKey('Role.id'), nullable=True)

    # Relations
    role = db.relationship('Role', back_populates='users')
    sent_messages = db.relationship('Message',
                                    foreign_keys='Message.Id_user_sender',
                                    back_populates='sender',
                                    lazy='dynamic')
    received_messages = db.relationship('Message',
                                        foreign_keys='Message.Id_user_recever',
                                        back_populates='receiver',
                                        lazy='dynamic')
    tokens = db.relationship('Token', back_populates='user', cascade='all, delete-orphan')

    def set_password(self, password):
        """Hash le mot de passe avec Argon2"""
        self.Password = ph.hash(password)

    def __repr__(self):
        return f'<User {self.Username}>'


class Role(db.Model):
    __tablename__ = 'Role'

    id = db.Column(db.String(191), primary_key=True)
    Name = db.Column(db.Text, nullable=False)

    # Relation inverse
    users = db.relationship('User', back_populates='role')

    def __repr__(self):
        return f'<Role {self.Name}>'


class Message(db.Model):
    __tablename__ = 'Message'

    id = db.Column(db.String(191), primary_key=True)
    Id_user_sender = db.Column(db.String(191), db.ForeignKey('User.id'), nullable=False)
    Id_user_recever = db.Column(db.String(191), db.ForeignKey('User.id'), nullable=False)
    Content = db.Column(db.LargeBinary, nullable=False)  # LongBlob
    Is_delivred = db.Column(db.Text, nullable=False)  # À remplacer par Boolean idéalement
    Date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relations
    sender = db.relationship('User', foreign_keys=[Id_user_sender], back_populates='sent_messages')
    receiver = db.relationship('User', foreign_keys=[Id_user_recever], back_populates='received_messages')

    # Index composite
    __table_args__ = (
        Index('idx_receiver_date', 'Id_user_recever', 'Date'),
    )

    def __repr__(self):
        return f'<Message {self.id} from {self.Id_user_sender}>'


class Token(db.Model):
    __tablename__ = 'Token'

    id = db.Column(db.String(191), primary_key=True)
    jwt_hash = db.Column(db.String(256), unique=True, nullable=False)
    id_user = db.Column(db.String(191), db.ForeignKey('User.id'), nullable=False)
    expired_at = db.Column(db.DateTime, nullable=False)
    is_revoked = db.Column(db.Boolean, default=False, nullable=False)
    creation_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_used = db.Column(db.DateTime, nullable=True)
    device_name = db.Column(db.Text, nullable=True)
    device_id = db.Column(db.String(191), unique=True, nullable=False)
    prev_hash = db.Column(db.String(64), nullable=True)

    # Relation
    user = db.relationship('User', back_populates='tokens')

    # Index composites
    __table_args__ = (
        Index('idx_user_expired', 'id_user', 'expired_at'),
    )

    def __repr__(self):
        return f'<Token {self.id} for user {self.id_user}>'


class Log(db.Model):
    __tablename__ = 'Log'

    id = db.Column(db.String(191), primary_key=True)
    action = db.Column(db.String(16), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    target_table = db.Column(db.String(32), nullable=False)
    target_id = db.Column(db.String(191), nullable=False)
    actor_user_id = db.Column(db.String(191), nullable=False)
    userId = db.Column(db.String(191), nullable=True)

    # Index multiples
    __table_args__ = (
        Index('idx_date', 'date'),
        Index('idx_action_date', 'action', 'date'),
        Index('idx_actor_date', 'actor_user_id', 'date'),
    )

    def __repr__(self):
        return f'<Log {self.action} on {self.target_table}>'