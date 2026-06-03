import uuid
from datetime import datetime, timedelta
import os

import jwt
from flask import Blueprint, render_template, request, jsonify, make_response
from sqlalchemy.exc import IntegrityError
from src.models import db, User, Token, ph
from src.utils import generate_cuid, get_user_by_email, verify_password, hash_token
from src.logger import logger

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/auth/register')
def register():
    return render_template('auth/register.html')


@auth_bp.route('/auth/login')
def login():
    return render_template('auth/login.html')


@auth_bp.route('/api/auth/register', methods=['POST'])
def api_register():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'message': 'Corps de requête JSON manquant'}), 400

    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '').strip()

    if not username or not email or not password:
        logger.warning("Register attempt with missing fields: username={}, email={}", bool(username), bool(email))
        return jsonify({'message': 'Tous les champs sont requis'}), 400

    if len(username) < 3:
        return jsonify({'message': 'Le nom d\'utilisateur doit faire au moins 3 caractères'}), 400

    try:
        user = User(
            id=generate_cuid(),
            Username=username,
            Email=email,
            Password=ph.hash(password),
            Is_verified=False,
            Is_activated=True,
            Id_role=None,
            Last_conection=datetime.utcnow(),
        )
        db.session.add(user)
        db.session.commit()
        logger.info("New user registered: username={}, email={}", username, email)
        return jsonify({'message': 'Compte créé avec succès'}), 201

    except IntegrityError as e:
        db.session.rollback()
        # Only use e.orig to avoid false matches in the full SQL query string
        orig = str(e.orig).lower() if e.orig else str(e).lower().split('[sql:')[0]
        logger.warning("Register IntegrityError for user={}: {}", username, orig)
        if 'username' in orig:
            return jsonify({'message': 'Ce nom d\'utilisateur est déjà pris'}), 409
        if 'email' in orig:
            return jsonify({'message': 'Cet email est déjà utilisé'}), 409
        return jsonify({'message': 'Nom d\'utilisateur ou email déjà utilisé'}), 409

    except Exception as e:
        db.session.rollback()
        logger.exception("Unexpected error during register for user={}", username)
        return jsonify({'message': 'Erreur interne du serveur'}), 500


@auth_bp.post('/api/auth/login')
def api_login():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'message': 'Corps de requête JSON manquant'}), 400

    identifier = data.get('identifier', '').strip()
    password = data.get('password', '').strip()
    remember = data.get('remember', False)

    if not identifier or not password:
        return jsonify({'message': 'Identifiant et mot de passe requis'}), 400

    user = get_user_by_email(identifier)
    if not user:
        logger.warning("Login attempt with unknown identifier: {}", identifier)
        return jsonify({'message': 'Email ou mot de passe incorrect'}), 401

    if not verify_password(password, user.Password):
        logger.warning("Failed login attempt for user: {}", user.Username)
        return jsonify({'message': 'Email ou mot de passe incorrect'}), 401

    access_payload = {
        'user_id': user.id,
        'exp': datetime.utcnow() + timedelta(minutes=10),
        'iat': datetime.utcnow(),
        'type': 'access'
    }
    access_token = jwt.encode(access_payload, os.getenv("JWT_SECRET"), algorithm='HS256')

    device_id = str(uuid.uuid4())

    refresh_payload = {
        'user_id': user.id,
        'device_id': device_id,
        'exp': datetime.utcnow() + timedelta(days=90),
        'iat': datetime.utcnow(),
        'type': 'refresh'
    }
    refresh_token = jwt.encode(refresh_payload, os.getenv("JWT_SECRET"), algorithm='HS256')

    try:
        token_record = Token(
            id=str(uuid.uuid4()),
            jwt_hash=hash_token(refresh_token),
            id_user=user.id,
            device_id=device_id,
            device_name=data.get('device_name') or request.headers.get('User-Agent', 'Unknown Device'),
            expired_at=datetime.utcnow() + timedelta(days=90),
        )
        db.session.add(token_record)

        user.Last_conection = datetime.utcnow()
        db.session.commit()
        logger.info("User logged in: {}", user.Username)
    except Exception:
        db.session.rollback()
        logger.exception("Error saving token for user={}", user.Username)
        return jsonify({'message': 'Erreur interne du serveur'}), 500

    response = make_response(jsonify({
        'message': 'Connexion réussie',
        'user': {
            'id': user.id,
            'username': user.Username,
            'email': user.Email
        }
    }), 200)
    response.set_cookie('access_token', access_token, httponly=True, max_age=10 * 60)
    response.set_cookie('refresh_token', refresh_token, httponly=True, max_age=90 * 24 * 60 * 60)

    return response


@auth_bp.post('/api/auth/logout')
def post_logout():
    user = request.current_user

    if not user:
        return jsonify({'message': 'Non authentifié'}), 401

    refresh_token = request.cookies.get('refresh_token')

    if refresh_token:
        try:
            token_hash = hash_token(refresh_token)
            token_record = Token.query.filter_by(jwt_hash=token_hash, id_user=user.id).first()
            if token_record:
                token_record.is_revoked = True
                db.session.commit()
                logger.info("Token revoked for user: {}", user.Username)
        except Exception:
            logger.exception("Error revoking token for user={}", user.Username)

    response = make_response(jsonify({'message': 'Déconnexion réussie'}), 200)
    response.set_cookie('access_token', '', httponly=True, max_age=0)
    response.set_cookie('refresh_token', '', httponly=True, max_age=0)

    return response
