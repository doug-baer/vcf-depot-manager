from flask import Blueprint, render_template, request, jsonify
from app.auth import requires_auth
from app.services.vcfdt import vcfdt_service

jobs_bp = Blueprint('jobs', __name__)

@jobs_bp.route('/jobs')
@requires_auth
def list_jobs():
    """View all download/configuration jobs."""
    jobs = vcfdt_service.list_jobs()
    return render_template('jobs.html', jobs=jobs)

@jobs_bp.route('/jobs/<job_id>')
@requires_auth
def view_job(job_id):
    """View details of a specific job."""
    status = vcfdt_service.get_job_status(job_id)
    return render_template('job_detail.html', job=status)

@jobs_bp.route('/jobs/api/status/<job_id>')
@requires_auth
def api_job_status(job_id):
    """JSON endpoint for polling job status."""
    status = vcfdt_service.get_job_status(job_id)
    return jsonify(status)

@jobs_bp.route('/jobs/api/last/<job_type>')
@requires_auth
def api_last_job(job_type):
    """Get output from the last job of a given type."""
    result = vcfdt_service.get_last_job_output(job_type)
    if result:
        return jsonify(result), 200
    return jsonify({'message': f'No jobs found of type {job_type}'}), 404