import os
from flask import Blueprint, render_template, request, redirect, url_for, send_from_directory
from app.auth import requires_auth
from app.services.depot_scanner import list_directory

depot_bp = Blueprint('depot', __name__)

DEPOT_STORE = os.environ.get('DEPOT_STORE', '/data/depot')


@depot_bp.route('/depot/')
@depot_bp.route('/depot/<path:subdir>')
@requires_auth
def browse(subdir=''):
    try:
        result = list_directory(DEPOT_STORE, subdir)
    except ValueError:
        return 'Forbidden', 403
    return render_template('depot.html', items=result['items'],
                           parent=result['parent'], current_path=subdir)


@depot_bp.route('/depot/files/<path:filepath>')
@requires_auth
def serve_file(filepath):
    """Serve a file from the depot - this is what SDDC Manager will hit."""
    return send_from_directory(DEPOT_STORE, filepath)