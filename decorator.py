import os
from functools import wraps

import jwt
from flask import request, jsonify
from utils import get_user_by_id


def jwt_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get('access_token')

        if not token:
            return jsonify({'message': 'Token manquant'}), 401

        try:
            data = jwt.decode(token, os.getenv("JWT_SECRET"), algorithms=['HS256'])

            if data.get('type') != 'access':
                return jsonify({'message': 'Type de token invalide'}), 401

            # Récupérer les infos user depuis la BDD (toujours à jour)
            user = get_user_by_id(data['user_id'])

            if not user:
                return jsonify({'message': 'Utilisateur non trouvé'}), 401

            # Ajouter l'objet user complet à la requête
            request.current_user = user

        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token expiré'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token invalide'}), 401

        return f(*args, **kwargs)

    return decorated