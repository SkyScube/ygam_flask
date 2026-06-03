from flask import Blueprint

from src.decorator import admin_required

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('panel')
@admin_required
def panel():

