from flask import Blueprint, jsonify
from models import *
from utils import generate_cuid

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """
    Welcome endpoint - Returns API information
    """
    return jsonify({
        'message': 'Welcome to Ygam API',
        'version': '0.1.0',
        'status': 'running',
        'endpoints': {
            'health': '/health',
            'docs': 'https://github.com/your-username/ygam'
        }
    })

@main_bp.route('/health')
def health():
    """
    Health check endpoint for Docker and monitoring
    """
    try:
        # Test database connection
        db.session.execute(db.text('SELECT 1'))
        db_status = 'connected'
    except Exception as e:
        db_status = 'error'
        print(f"Database health check failed: {e}")

    return jsonify({
        'status': 'ok',
        'database': db_status,
        'version': '0.1.0'
    }), 200 if db_status == 'connected' else 503