import secrets
import string
import hashlib
from argon2.exceptions import VerifyMismatchError
from src.models import *

def generate_cuid():
    """Génère un ID unique similaire à cuid de Prisma"""
    return 'c' + ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(24))

def get_user_by_email(email: str):
    return db.session.query(User).filter(User.Email == email).first()

def get_user_by_identifier(identifier: str):
    return db.session.query(User).filter(
        (User.Email == identifier) | (User.Username == identifier)
    ).first()


def verify_password(plain: str, hashed: str) -> bool:
    try:
        ph.verify(hashed, plain)
        return True
    except VerifyMismatchError:
        return False

def get_user_by_id(user_id: str):
    return db.session.query(User).filter(User.id == user_id).first()

def hash_token(token: str) -> str:
    """Hash déterministe pour les tokens JWT (utilise SHA256 au lieu d'Argon2)"""
    return hashlib.sha256(token.encode()).hexdigest()