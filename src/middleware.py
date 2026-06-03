import os

import jwt
from flask import request, current_app
from src.models import db, Token
from datetime import datetime, timedelta

from src.utils import get_user_by_id, hash_token


def get_token_record(refresh_token):
    """
    Helper function to retrieve token record from database.
    Returns token_record or None if not found.
    """
    if not refresh_token:
        return None

    token_hash = hash_token(refresh_token)
    token_record = Token.query.filter_by(jwt_hash=token_hash).first()
    return token_record


def authenticate_and_refresh():
    """
    Charge l'utilisateur si tokens présents et valides.
    Refresh automatiquement si access token expiré.
    NE BLOQUE PAS les routes publiques.
    """
    # Public routes (including Socket.IO endpoints)
    if request.endpoint in ['auth.api_login', 'auth.api_register', 'static', None] or \
       (request.endpoint and request.endpoint.startswith('socketio')):
        return None

    access_token = request.cookies.get('access_token')
    refresh_token = request.cookies.get('refresh_token')

    # No tokens -> pass through; @jwt_required will block if needed
    if not access_token and not refresh_token:
        request.current_user = None
        return None

    user_id = None

    # Try access token
    if access_token:
        try:
            data = jwt.decode(access_token, os.getenv("JWT_SECRET"), algorithms=['HS256'])
            if data.get('type') == 'access':
                user_id = data['user_id']
        except jwt.ExpiredSignatureError:
            pass  # Will attempt refresh below
        except jwt.InvalidTokenError:
            request.current_user = None
            return None

    # If access expired, try refresh token
    if not user_id and refresh_token:
        try:
            refresh_data = jwt.decode(refresh_token, os.getenv("JWT_SECRET"), algorithms=['HS256'])

            if refresh_data.get('type') == 'refresh':
                token_record = get_token_record(refresh_token)

                if token_record and not token_record.is_revoked and token_record.expired_at > datetime.utcnow():
                    user_id = refresh_data['user_id']

                    # Generate new access token
                    new_access_token = jwt.encode({
                        'user_id': user_id,
                        'exp': datetime.utcnow() + timedelta(minutes=10),
                        'iat': datetime.utcnow(),
                        'type': 'access'
                    }, os.getenv("JWT_SECRET"), algorithm='HS256')

                    request._new_access_token = new_access_token

                    # Update last_used
                    token_record.last_used = datetime.utcnow()
                    db.session.commit()
        except Exception:
            pass

    # Load user if we have a user_id
    if user_id:
        token_record = get_token_record(refresh_token)

        if not token_record:
            return None

        request.current_user = get_user_by_id(user_id)
    else:
        request.current_user = None

    return None


def inject_new_access_token(response):
    if hasattr(request, '_new_access_token'):
        is_production = os.getenv('FLASK_ENV') == 'production'
        response.set_cookie(
            'access_token',
            request._new_access_token,
            httponly=True,
            secure=is_production,
            samesite='Strict',
            max_age=15 * 60
        )
    return response


def register_middleware(app):
    """Register middleware hooks with the Flask app."""
    app.before_request(authenticate_and_refresh)
    app.after_request(inject_new_access_token)
