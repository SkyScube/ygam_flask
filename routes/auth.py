from flask import Blueprint, render_template, request, jsonify
from models import *
from utils import generate_cuid

auth_bp = Blueprint('auth', __name__)
ph = PasswordHasher()

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
    user = User(
        id=generate_cuid(),
        Username=username,
        Email=email,
        Password=ph.hash(password), # Hash en argon2 du hash SHA256*1000 du client
        Is_verified=False,
        Is_activaded=True,
        Id_role=2,
        Last_conection=datetime
    )
    db.session.add(user)
    db.session.commit()
    print(username, email, password)
    return jsonify({
        'message': 'Compte créé avec succès'
    }), 201

@auth_bp.route('/api/auth/login', methods=['POST'])
def api_login():
    identifier = request.json.get('identifier')
    password = request.json.get('password')
    remember = request.json.get('remember', False)
    print(identifier, password, remember)
    # TODO: Implémenter la logique de connexion
    return jsonify({
        'message': 'Connexion réussie',
        'access_token': 'fake_access_token',
        'refresh_token': 'fake_refresh_token'
    }), 200