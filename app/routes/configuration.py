from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.auth import requires_auth
from app.services.vcfdt import vcfdt_service

configuration_bp = Blueprint('configuration', __name__)

@configuration_bp.route('/configuration', methods=['GET'])
@requires_auth
def configuration_page():
    """Display depot ID and activation code status."""
    depot_id = vcfdt_service.get_depot_id()
    has_activation = vcfdt_service.has_activation_code()

    return render_template('configuration.html',
                           depot_id=depot_id,
                           has_activation=has_activation)

@configuration_bp.route('/configuration/generate-depot-id', methods=['POST'])
@requires_auth
def generate_depot_id():
    """Trigger depot ID generation."""
    result = vcfdt_service.generate_depot_id()

    if result['success']:
        flash(f'Software Depot ID generated: {result["depot_id"][:20]}...', 'success')
    else:
        flash(f'Depot ID generation failed: {result.get("stderr", "Unknown error")}', 'error')

    return redirect(url_for('configuration.configuration_page'))

@configuration_bp.route('/configuration/save-activation-code', methods=['POST'])
@requires_auth
def save_activation_code():
    """Save the Broadcom activation code (after registering depot ID)."""
    if 'activation_code' not in request.files:
        # Try form input instead
        code_text = request.form.get('activation_code', '').strip()
        if not code_text:
            flash('No activation code provided', 'error')
            return redirect(url_for('configuration.configuration_page'))
        vcfdt_service.save_activation_code(code_text)
    else:
        file = request.files['activation_code']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(url_for('configuration.configuration_page'))
        code_text = file.read().decode('utf-8')
        vcfdt_service.save_activation_code(code_text)

    flash('Activation code saved successfully', 'success')
    return redirect(url_for('configuration.configuration_page'))

@configuration_bp.route('/configuration/api/depot-id')
@requires_auth
def api_depot_id():
    """JSON API endpoint to get depot ID."""
    depot_id = vcfdt_service.get_depot_id()
    if depot_id:
        return jsonify({'success': True, 'depot_id': depot_id}), 200
    return jsonify({'success': False, 'message': 'No depot ID generated yet'}), 404