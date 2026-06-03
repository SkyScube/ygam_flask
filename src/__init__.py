import os
from flask import Flask, jsonify


def create_app(create_tables=None):
    from src.models import db
    from src.config import Config
    from src.extensions import socketio
    from src.logger import logger

    app = Flask(__name__)
    app.config.from_object(Config)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

    db.init_app(app)
    socketio.init_app(app, cors_allowed_origins='*', async_mode='threading')

    # Blueprints
    from src.routes.main import main_bp
    from src.routes.auth import auth_bp
    from src.routes.chat import chat_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(chat_bp)

    # HTTP middleware (before/after_request)
    from src.middleware import register_middleware
    register_middleware(app)

    # Socket.IO events
    from src.sockets import register_sockets
    register_sockets(socketio)

    # Global error handlers — log ALL unhandled exceptions
    @app.errorhandler(Exception)
    def handle_exception(e):
        logger.exception("Unhandled exception on {} {}", app.debug, str(e))
        return jsonify({'message': 'Erreur interne du serveur'}), 500

    @app.errorhandler(404)
    def handle_404(e):
        return jsonify({'message': 'Route introuvable'}), 404

    @app.errorhandler(405)
    def handle_405(e):
        return jsonify({'message': 'Méthode non autorisée'}), 405

    # Create DB tables
    if create_tables is None:
        create_tables = os.getenv('FLASK_CREATE_TABLES', 'false').lower() == 'true'

    if create_tables:
        with app.app_context():
            try:
                db.create_all()
                logger.info("Database tables created successfully")
            except Exception as e:
                logger.error("Could not create database tables: {}", e)

    return app
