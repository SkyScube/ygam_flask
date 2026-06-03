import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY                   = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_DATABASE_URI      = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS    = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }

    # Client simulation DB — separate SQLite file
    _base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    CLIENT_DB_PATH = os.getenv(
        'CLIENT_DB_PATH',
        os.path.join(_base_dir, 'client_data', 'client_sim.db')
    )
    SQLALCHEMY_BINDS = {
        'client': f"sqlite:///{CLIENT_DB_PATH}"
    }
