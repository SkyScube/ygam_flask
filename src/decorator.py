from functools import wraps
from flask import request, jsonify, redirect, url_for


def jwt_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if hasattr(request, 'current_user') and request.current_user:
            return f(*args, **kwargs)

        # API routes and explicit JSON requests always get 401 JSON, never a redirect
        wants_json = (
            request.is_json
            or request.headers.get('Accept') == 'application/json'
            or request.path.startswith('/api/')
        )
        if wants_json:
            return jsonify({'message': 'Authentication required'}), 401

        return redirect(url_for('auth.login'))

    return decorated
