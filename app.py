from flask import Flask
from models import db
from config import Config

# Créer l'instance app au niveau module
app = Flask(__name__)
app.config.from_object(Config)

# Initialiser SQLAlchemy
db.init_app(app)

# Enregistrer les blueprints
from routes.main import main_bp
from routes.auth import auth_bp
app.register_blueprint(main_bp)
app.register_blueprint(auth_bp)

# Import du middleware APRÈS la création de app
import middleware

# Créer les tables
with app.app_context():
    db.create_all()


if __name__ == '__main__':
    app.run(debug=True)