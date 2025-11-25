from flask import Flask
from models import db
from config import Config


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialiser SQLAlchemy
    db.init_app(app)

    # Enregistrer les blueprints
    from routes.main import main_bp
    app.register_blueprint(main_bp)

    # Créer les tables
    with app.app_context():
        db.create_all()

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)