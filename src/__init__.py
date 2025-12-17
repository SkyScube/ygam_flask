import os
from flask import Flask


def create_app(create_tables=None):
    """Factory function to create and configure the Flask application.

    Args:
        create_tables: If True, creates database tables on startup.
                      If None (default), checks FLASK_CREATE_TABLES env var.
                      Set to False to skip table creation.
    """
    # Import inside function to avoid circular imports
    from src.models import db
    from src.config import Config

    # Create Flask app
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize database
    db.init_app(app)

    # Register blueprints (import inside function)
    from src.routes.main import main_bp
    from src.routes.auth import auth_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)

    # Register middleware (must be done after app creation)
    from src.middleware import register_middleware
    register_middleware(app)

    # Create database tables based on parameter or environment variable
    if create_tables is None:
        # Check environment variable (default to False for flask run)
        create_tables = os.getenv('FLASK_CREATE_TABLES', 'false').lower() == 'true'

    if create_tables:
        with app.app_context():
            try:
                db.create_all()
                app.logger.info("Database tables created successfully")
            except Exception as e:
                app.logger.warning(f"Could not create database tables: {e}")
                app.logger.warning("Run 'flask db create' manually or start your database service")

    return app