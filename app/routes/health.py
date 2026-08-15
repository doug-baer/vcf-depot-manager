import os
from flask import Blueprint, jsonify, render_template
from app.services.vcfdt import vcfdt_service

health_bp = Blueprint('health', __name__)

@health_bp.route('/health')
def health():
    data = {
        'status': 'healthy',
        'vcfdt_binary': os.path.isfile(os.environ.get('VCFDT_BIN_PATH', '/opt/vcfdt/vcf-download-tool')),
        'depot_exists': os.path.isdir(os.environ.get('DEPOT_STORE', '/data/depot')),
        'has_token': vcfdt_service.has_active_token(),
    }
    # JSON for health checks, HTML for humans
    from flask import request
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        return jsonify(data), 200 if data['vcfdt_binary'] else 503
    return render_template('health.html', **data)