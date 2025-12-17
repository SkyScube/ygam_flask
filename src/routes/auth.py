import uuid
from datetime import datetime, timedelta
import os

import jwt
from flask import Blueprint, render_template, request, jsonify, make_response
from src.models import *
from src.utils import generate_cuid, get_user_by_email, verify_password, hash_token

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
            Password=ph.hash(password), # Argon2 hash of SHA256*1000 client-side hash
            Is_verified=False,
            Is_activaded=True,
            Id_role=2,
            Last_conection=datetime.utcnow(),
        )
        db.session.add(user)
        db.session.commit()

        print(username, email, password)
        return jsonify({
            'message': 'Account created successfully'
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
    user = get_user_by_email(identifier)
    if not user:
        return jsonify({
            'message': 'Email or password incorrect',
        }), 401
    if not verify_password(password, user.Password):
        return jsonify({
            'message': 'Email or password incorrect',
        }), 401

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

    token_record = Token(
        id=str(uuid.uuid4()),
        jwt_hash=hash_token(refresh_token),
        id_user=user.id,
        device_id=device_id,
        device_name=request.json.get('device_name') or request.headers.get('User-Agent', 'Unknown Device'),
        expired_at=datetime.utcnow() + timedelta(days=90),
    )
    db.session.add(token_record)
    db.session.commit()

    response = make_response(jsonify({
        'message': 'Login successful',
        'user': {
            'id': user.id,
            'username': user.Username,
            'email': user.Email
        }
    }), 200)
    response.set_cookie('access_token', access_token, httponly=True, max_age=10*60) # 10min
    response.set_cookie('refresh_token', refresh_token, httponly=True, max_age=90*24*60*60) # 90min

    return response

@auth_bp.post('/api/auth/logout')
def post_logout():
    user = request.current_user

    if not user:
        return jsonify({
            'message': 'Not authenticated'
        }), 401

    refresh_token = request.cookies.get('refresh_token')

    if refresh_token:
        try:
            token_hash = hash_token(refresh_token)
            token_record = Token.query.filter_by(jwt_hash=token_hash, id_user=user.id).first()

            if token_record:
                token_record.is_revoked = True
                db.session.commit()
        except Exception as e:
            print(f"Error revoking token: {e}")

    response = make_response(jsonify({
        'message': 'Logout successful'
    }), 200)

    response.set_cookie('access_token', '', httponly=True, max_age=0)
    response.set_cookie('refresh_token', '', httponly=True, max_age=0)

    return response
