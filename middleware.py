import os

import jwt
from flask import request

from app import app
from models import ph, db, Token
from datetime import datetime, timedelta

from utils import get_user_by_id, hash_token


def get_token_record(refresh_token):
    """
    Helper function to retrieve token record from database
    Returns token_record or None if not found
    """
    if not refresh_token:
        return None

    token_hash = hash_token(refresh_token)
    print(f"🔐 [HELPER] Hash calculated: {token_hash}")
    token_record = Token.query.filter_by(jwt_hash=token_hash).first()

    if token_record:
        print(f"✅ [HELPER] Token found in DB: id={token_record.id}, revoked={token_record.is_revoked}")
    else:
        print("❌ [HELPER] Token NOT FOUND in DB")

    return token_record


@app.before_request
def authenticate_and_refresh():
    """
    Charge l'utilisateur si tokens présents et valides
    Refresh automatiquement si access token expiré
    NE BLOQUE PAS les routes publiques
    """
    print(f"🔍 [MIDDLEWARE] Requête vers: {request.endpoint}")

    # Routes publiques
    if request.endpoint in ['auth.api_login', 'auth.api_register', 'static']:
        print("✅ [MIDDLEWARE] Route publique, on laisse passer")
        return None

    access_token = request.cookies.get('access_token')
    refresh_token = request.cookies.get('refresh_token')

    print(f"🍪 [MIDDLEWARE] access_token présent: {bool(access_token)}")
    print(f"🍪 [MIDDLEWARE] refresh_token présent: {bool(refresh_token)}")

    # ✅ Pas de tokens → OK, on laisse passer
    # Le decorator @login_required bloquera si nécessaire
    if not access_token and not refresh_token:
        print("⚠️ [MIDDLEWARE] Aucun token, on laisse passer")
        request.current_user = None
        return None

    user_id = None

    # Essayer l'access token
    if access_token:
        try:
            data = jwt.decode(access_token, os.getenv("JWT_SECRET"), algorithms=['HS256'])
            if data.get('type') == 'access':
                user_id = data['user_id']
                print(f"✅ [MIDDLEWARE] Access token valide, user_id: {user_id}")
        except jwt.ExpiredSignatureError:
            print("⏰ [MIDDLEWARE] Access token EXPIRÉ, on va tenter le refresh")
            pass  # On va utiliser le refresh token
        except jwt.InvalidTokenError as e:
            print(f"❌ [MIDDLEWARE] Access token invalide: {e}")
            request.current_user = None
            return None

    # ✅ Si access expiré, utiliser le refresh token
    if not user_id and refresh_token:
        print("🔄 [MIDDLEWARE] Tentative de refresh...")
        try:
            refresh_data = jwt.decode(refresh_token, os.getenv("JWT_SECRET"), algorithms=['HS256'])
            print(f"✅ [MIDDLEWARE] Refresh token décodé: user_id={refresh_data.get('user_id')}")

            if refresh_data.get('type') == 'refresh':
                # Verify in database
                token_record = get_token_record(refresh_token)

                if token_record and not token_record.is_revoked and token_record.expired_at > datetime.utcnow():
                    user_id = refresh_data['user_id']
                    print(f"🎉 [MIDDLEWARE] Token valide ! Génération nouveau access token...")

                    # ✅ Générer nouveau access token
                    new_access_token = jwt.encode({
                        'user_id': user_id,
                        'exp': datetime.utcnow() + timedelta(minutes=10),
                        'iat': datetime.utcnow(),
                        'type': 'access'
                    }, os.getenv("JWT_SECRET"), algorithm='HS256')

                    request._new_access_token = new_access_token
                    print(f"✅ [MIDDLEWARE] Nouveau access token généré et stocké dans request._new_access_token")

                    # Mettre à jour last_used
                    token_record.last_used = datetime.utcnow()
                    db.session.commit()
                    print("✅ [MIDDLEWARE] last_used mis à jour en DB")
                else:
                    print("❌ [MIDDLEWARE] Token invalide ou révoqué ou expiré")
        except Exception as e:
            print(f"❌ [MIDDLEWARE] Erreur lors du refresh: {e}")
            pass

    # ✅ Load user if we have a user_id
    if user_id:
        token_record = get_token_record(refresh_token)

        if not token_record:
            return None

        request.current_user = get_user_by_id(user_id)
        print(f"✅ [MIDDLEWARE] Utilisateur chargé: {request.current_user.Username if request.current_user else 'None'}")
    else:
        request.current_user = None
        print("⚠️ [MIDDLEWARE] Aucun user_id, current_user = None")

    return None


@app.after_request
def inject_new_access_token(response):
    print(f"🔄 [AFTER_REQUEST] Vérification de request._new_access_token...")
    if hasattr(request, '_new_access_token'):
        print(f"🎉 [AFTER_REQUEST] Nouveau access token trouvé ! Injection dans les cookies...")
        is_production = os.getenv('FLASK_ENV') == 'production'
        response.set_cookie('access_token', request._new_access_token, httponly=True, secure=is_production,
                            samesite='Strict', max_age=15 * 60)
        print(f"✅ [AFTER_REQUEST] Cookie access_token mis à jour dans la réponse")
    else:
        print(f"⚠️ [AFTER_REQUEST] Pas de nouveau access token à injecter")
    return response