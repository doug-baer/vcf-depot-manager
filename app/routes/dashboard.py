from flask import Blueprint, render_template
from app.auth import requires_auth
from app.services.depot_scanner import scan_depot
from app.services.vcfdt import vcfdt_service
import os

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@requires_auth
def index():
    depot_path = os.environ.get('DEPOT_STORE', '/data/depot')
    depot_info = scan_depot(depot_path)
    jobs = vcfdt_service.list_jobs()
    has_token = vcfdt_service.has_active_token()

    return render_template('dashboard.html',
                           depot=depot_info,
                           jobs=jobs,
                           has_token=has_token)