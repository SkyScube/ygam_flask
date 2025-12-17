import os
from functools import wraps

import jwt
from flask import request, jsonify, redirect, url_for
from src.utils import get_user_by_id


def jwt_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if hasattr(request, 'current_user') and request.current_user:
            return f(*args, **kwargs)

        if request.is_json or request.headers.get('Accept') == 'application/json':
            return jsonify({
                'message': 'Authentication required',
                'redirect': '/auth/login'
            }), 401

        return redirect(url_for('auth.login'))

    return decorated