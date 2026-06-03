import os
from flask import Flask, jsonify


def create_app(create_tables=None):
    from src.models import db, seed_roles
    from src.config import Config
    from src.extensions import socketio
    from src.logger import logger

    app = Flask(__name__)
    app.config.from_object(Config)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

    # Ensure client_data dir exists for SQLite
    client_db_path = app.config.get('CLIENT_DB_PATH', '')
    if client_db_path and os.path.dirname(client_db_path):
        os.makedirs(os.path.dirname(client_db_path), exist_ok=True)

    db.init_app(app)
    socketio.init_app(app, cors_allowed_origins='*', async_mode='threading')

    # Blueprints
    from src.routes.main import main_bp
    from src.routes.auth import auth_bp
    from src.routes.chat import chat_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(chat_bp)

    # HTTP middleware
    from src.middleware import register_middleware
    register_middleware(app)

    # Socket.IO events
    from src.sockets import register_sockets
    register_sockets(socketio)

    # Global error handlers
    @app.errorhandler(Exception)
    def handle_exception(e):
        logger.exception("Unhandled exception: {}", str(e))
        return jsonify({'message': 'Erreur interne du serveur'}), 500

    @app.errorhandler(404)
    def handle_404(e):
        return jsonify({'message': 'Route introuvable'}), 404

    @app.errorhandler(405)
    def handle_405(e):
        return jsonify({'message': 'Méthode non autorisée'}), 405

    # DB tables
    if create_tables is None:
        create_tables = os.getenv('FLASK_CREATE_TABLES', 'false').lower() == 'true'

    if create_tables:
        import time
        import src.client_models  # noqa: F401 — registers models before create_all
        with app.app_context():
            for attempt in range(1, 11):
                try:
                    db.create_all()
                    logger.info("Database tables created successfully")
                    seed_roles()
                    logger.info("Roles seeded")
                    break
                except Exception as e:
                    if attempt == 10:
                        logger.error("Could not initialize database after 10 attempts: {}", e)
                    else:
                        logger.warning("DB not ready (attempt {}/10), retrying in {}s...", attempt, attempt * 2)
                        time.sleep(attempt * 2)

    return app
