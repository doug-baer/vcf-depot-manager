from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.auth import requires_auth
from app.services.vcfdt import vcfdt_service

downloads_bp = Blueprint('downloads', __name__)


@downloads_bp.route('/downloads', methods=['GET'])
@requires_auth
def downloads_page():
    jobs = vcfdt_service.list_jobs()
    return render_template('downloads.html', jobs=jobs)


@downloads_bp.route('/downloads/start', methods=['POST'])
@requires_auth
def start_download():
    if not vcfdt_service.has_active_token():
        flash('No active download token. Please upload one first.', 'error')
        return redirect(url_for('downloads.downloads_page'))

    data = request.form
    job_id = vcfdt_service.start_download(
        vcf_version=data.get('vcf_version', '9.1.0'),
        download_type=data.get('download_type', 'INSTALL'),
        component=data.get('component') or None,
        patches_only=data.get('patches_only') == 'on',
        component_version=data.get('component_version') or None,
    )
    flash(f'Download job {job_id} started.', 'success')
    return redirect(url_for('downloads.downloads_page'))


@downloads_bp.route('/downloads/status/<job_id>')
@requires_auth
def job_status(job_id):
    status = vcfdt_service.get_job_status(job_id)
    return jsonify(status)