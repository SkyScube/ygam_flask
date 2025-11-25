from flask import Blueprint, jsonify
from models import *
from utils import generate_cuid

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    user = User.query.all()
    print(user)
    return jsonify([{'id': u.id, 'username': u.Username, 'password': u.Password} for u in user])