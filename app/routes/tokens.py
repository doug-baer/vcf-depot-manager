from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.auth import requires_auth
from app.services.vcfdt import vcfdt_service

tokens_bp = Blueprint('tokens', __name__)


@tokens_bp.route('/token', methods=['GET', 'POST'])
@requires_auth
def manage_token():
    if request.method == 'POST':
        if 'token_file' not in request.files:
            flash('No file uploaded.', 'error')
            return redirect(request.url)

        file = request.files['token_file']
        if file.filename == '':
            flash('No file selected.', 'error')
            return redirect(request.url)

        token_content = file.read().decode('utf-8')
        token_path = vcfdt_service.save_token(token_content)
        flash(f'Token saved and activated: {token_path}', 'success')
        return redirect(url_for('dashboard.index'))

    has_token = vcfdt_service.has_active_token()
    return render_template('token.html', has_token=has_token)