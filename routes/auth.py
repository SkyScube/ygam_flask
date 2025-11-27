import uuid
from datetime import datetime, timezone, timedelta
import os

import jwt
from flask import Blueprint, render_template, request, jsonify, make_response
from models import *
from utils import generate_cuid, get_user_by_email, verify_password

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/auth/register')
def register():
    return render_template('auth/register.html')

@auth_bp.route('/auth/login')
def login():
    return render_template('auth/login.html')

@auth_bp.route('/api/auth/register', methods=['POST'])
def api_register():
    username = request.json.get('username')
    email = request.json.get('email')
    password = request.json.get('password')
    print(datetime.utcnow())
    try:
        user = User(
            id=generate_cuid(),
            Username=username,
            Email=email,
            Password=ph.hash(password), # Hash en argon2 du hash SHA256*1000 du client
            Is_verified=False,
            Is_activaded=True,
            Id_role=2,
            Last_conection=datetime.utcnow(),
        )
        db.session.add(user)
        db.session.commit()

        print(username, email, password)
        return jsonify({
            'message': 'Compte créé avec succès'
        }), 201
    except Exception as e:
        return jsonify({
            'message': 'Internal Server Error',
        }), 500

@auth_bp.post('/api/auth/login')
def api_login():
    identifier = request.json.get('identifier')
    password = request.json.get('password')
    remember = request.json.get('remember', False)
    print(identifier, password, remember)
    user = get_user_by_email(identifier)
    if not user:
        return jsonify({
            'message': 'mail or password incorrect',
        })
    if not verify_password(password, user.Password):
        return jsonify({
            'message': 'mail or password incorrect',
        })

    access_payload = {
        'user_id': user.id,
        'exp': datetime.now(timezone.utc) + timedelta(minutes=10),
        'iat': datetime.now(timezone.utc),
        'type': 'access'
    }
    access_token = jwt.encode(access_payload, os.getenv("JWT_SECRET"), algorithm='HS256')

    device_id = str(uuid.uuid4())

    refresh_payload = {
        'user_id': user.id,
        'device_id': device_id,
        'exp': datetime.now(timezone.utc) + timedelta(days=90),
        'iat': datetime.now(timezone.utc),
        'type': 'refresh'
    }
    refresh_token = jwt.encode(refresh_payload, os.getenv("JWT_SECRET"), algorithm='HS256')

    token_record = Token(
        id=str(uuid.uuid4()),
        jwt_hash=ph.hash(refresh_token),
        id_user=user.id,
        device_id=device_id,
        device_name=request.get_data(),
        expired_at=datetime.now(timezone.utc) + timedelta(days=90),
    )
    db.session.add(token_record)
    db.session.commit()

    response = make_response(jsonify({
        'message': 'Connexion réussie',
        'user': {
            'id': user.id,
            'username': user.Username,
            'email': user.Email
        }
    }), 200)
    response.set_cookie('access_token', access_token, httponly=True, max_age=10*60) # 10min
    response.set_cookie('refresh_token', refresh_token, httponly=True, max_age=90*24*60*60) # 90min

    return response


# auth/routes.py
@auth_bp.post('/api/auth/refresh')
def refresh():
    refresh_token_value = request.cookies.get('refresh_token')

    if not refresh_token_value:
        return jsonify({'message': 'Refresh token manquant'}), 401

    try:
        # ✅ Décoder le refresh token
        data = jwt.decode(refresh_token_value, os.getenv("JWT_SECRET"), algorithms=['HS256'])

        if data.get('type') != 'refresh':
            return jsonify({'message': 'Type de token invalide'}), 401

        user_id = data['user_id']
        device_id = data['device_id']  # ✅ Récupéré depuis le JWT

        # ✅ Vérifier en BDD
        token_hash = ph.hash(refresh_token_value)
        token_record = Token.query.filter_by(jwt_hash=token_hash).first()

        if not token_record:
            return jsonify({'message': 'Token invalide'}), 401

        if token_record.is_revoked:
            return jsonify({'message': 'Token révoqué'}), 401

        if token_record.expired_at < datetime.now(timezone.utc):
            return jsonify({'message': 'Token expiré'}), 401

        # ✅ Mettre à jour last_used
        token_record.last_used = datetime.now(timezone.utc)
        db.session.commit()

        # ✅ Créer un nouveau access token
        access_payload = {
            'user_id': user_id,
            'exp': datetime.now(timezone.utc) + timedelta(minutes=15),
            'iat': datetime.now(timezone.utc),
            'type': 'access'
        }
        new_access_token = jwt.encode(access_payload, os.getenv("JWT_SECRET"), algorithm='HS256')

        response = make_response(jsonify({'message': 'Token rafraîchi'}), 200)

        is_production = os.getenv('FLASK_ENV') == 'production'

        response.set_cookie('access_token', new_access_token, httponly=True, secure=is_production, samesite='Strict',
                            max_age=15 * 60)

        return response

    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Refresh token expiré'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'message': 'Token invalide'}), 401