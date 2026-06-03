from flask import Blueprint, jsonify, request
from src.decorator import jwt_required
from src.models import db
from src.logger import logger

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
@jwt_required
def index():
    return jsonify({
        'message': 'Welcome to Ygam API',
        'version': '0.1.0',
        'status': 'running',
        'username': request.current_user.Username,
        'email': request.current_user.Email,
    })


@main_bp.route('/health')
def health():
    try:
        db.session.execute(db.text('SELECT 1'))
        db_status = 'connected'
    except Exception as e:
        db_status = 'error'
        logger.error("Database health check failed: {}", e)

    return jsonify({
        'status': 'ok',
        'database': db_status,
        'version': '0.1.0'
    }), 200 if db_status == 'connected' else 503