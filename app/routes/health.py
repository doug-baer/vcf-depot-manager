import os
from flask import Blueprint, jsonify, render_template, request
from app.services.vcfdt import vcfdt_service

health_bp = Blueprint('health', __name__)

@health_bp.route('/health')
def health():
    data = {
        'status': 'healthy',
        'vcfdt_binary': os.path.isfile(os.environ.get('VCFDT_BIN_PATH', '/opt/vcfdt/bin/vcf-download-tool')),
        'depot_exists': os.path.isdir(os.environ.get('DEPOT_STORE', '/data/depot')),
        'has_depot_id': vcfdt_service.has_depot_id(),
        'has_activation_code': vcfdt_service.has_activation_code(),
    }
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        return jsonify(data), 200 if data['vcfdt_binary'] else 503
    return render_template('health.html', **data)