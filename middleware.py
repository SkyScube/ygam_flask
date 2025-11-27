import os

import jwt
from flask import request

from models import ph, db
from datetime import datetime, timezone, timedelta

from utils import get_user_by_id


@app.before_request
def authenticate_and_refresh():
    """
    Charge l'utilisateur si tokens présents et valides
    Refresh automatiquement si access token expiré
    NE BLOQUE PAS les routes publiques
    """

    # Routes publiques
    if request.endpoint in ['auth.api_login', 'auth.api_register', 'static']:
        return None

    access_token = request.cookies.get('access_token')
    refresh_token = request.cookies.get('refresh_token')

    # ✅ Pas de tokens → OK, on laisse passer
    # Le decorator @login_required bloquera si nécessaire
    if not access_token and not refresh_token:
        request.current_user = None
        return None

    user_id = None

    # Essayer l'access token
    if access_token:
        try:
            data = jwt.decode(access_token, os.getenv("JWT_SECRET"), algorithms=['HS256'])
            if data.get('type') == 'access':
                user_id = data['user_id']
        except jwt.ExpiredSignatureError:
            pass  # On va utiliser le refresh token
        except jwt.InvalidTokenError:
            request.current_user = None
            return None

    # ✅ Si access expiré, utiliser le refresh token
    if not user_id and refresh_token:
        try:
            refresh_data = jwt.decode(refresh_token, os.getenv("JWT_SECRET"), algorithms=['HS256'])

            if refresh_data.get('type') == 'refresh':
                # Vérifier en BDD
                from models import Token

                token_hash = ph.hash(refresh_token)
                token_record = Token.query.filter_by(jwt_hash=token_hash).first()

                if token_record and not token_record.is_revoked and token_record.expired_at > datetime.now(timezone.utc):
                    user_id = refresh_data['user_id']

                    # ✅ Générer nouveau access token
                    new_access_token = jwt.encode({
                        'user_id': user_id,
                        'exp': datetime.now(timezone.utc) + timedelta(minutes=10),
                        'iat': datetime.now(timezone.utc),
                        'type': 'access'
                    }, os.getenv("JWT_SECRET"), algorithm='HS256')

                    request._new_access_token = new_access_token

                    # Mettre à jour last_used
                    token_record.last_used = datetime.now(timezone.utc)
                    db.session.commit()
        except:
            pass

    # ✅ Charger l'utilisateur si on a un user_id
    if user_id:
        request.current_user = get_user_by_id(user_id)
    else:
        request.current_user = None

    return None


@app.after_request
def inject_new_access_token(response):
    if hasattr(request, '_new_access_token'):
        is_production = os.getenv('FLASK_ENV') == 'production'
        response.set_cookie('access_token', request._new_access_token, httponly=True, secure=is_production,
                            samesite='Strict', max_age=15 * 60)
    return response