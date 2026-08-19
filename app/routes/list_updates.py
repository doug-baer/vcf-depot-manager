from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.auth import requires_auth
from app.services.vcfdt import vcfdt_service

list_updates_bp = Blueprint('list_updates', __name__)

@list_updates_bp.route('/list-updates', methods=['GET', 'POST'])
@requires_auth
def list_updates():
    """Query and display available VCF updates/components."""
    result = None
    
    # Form submission to trigger the list command
    if request.method == 'POST':
        vcf_version = request.form.get('vcf_version', '9.1.0')
        download_type = request.form.get('download_type', 'INSTALL')  # INSTALL or UPGRADE
        component = request.form.get('component', '') or None
        
        result = vcfdt_service.list_binaries(
            vcf_version=vcf_version,
            download_type=download_type,
            component=component
        )
        
        if result['success']:
            flash(f'Listed {len(result["stdout"].split(chr(10)))} lines of output', 'success')
        else:
            flash(f'List command failed: {result.get("stderr", "Unknown error")}', 'error')
    
    # Pre-filled form values for the page
    return render_template('list_updates.html', result=result, default_vcf_version='9.1.0')

import re

@list_updates_bp.route('/api/list-updates')
@requires_auth
def api_list_updates():
    """JSON API that parses the list output into structured data."""
    vcf_version = request.args.get('vcf_version', '9.1.0')
    download_type = request.args.get('download_type', 'INSTALL')
    component = request.args.get('component') or None
    
    result = vcfdt_service.list_binaries(
        vcf_version=vcf_version,
        download_type=download_type,
        component=component
    )
    
    if not result['success']:
        return {'success': False, 'error': result.get('stderr', 'Unknown error')}, 500
    
    # Parse the output into structured data (adjust regex based on actual VCFDT output format)
    lines = result['stdout'].strip().split('\n')
    components = []
    
    for line in lines:
        # Example VCFDT list output parsing — adjust pattern to match actual output
        # Format might look like: "ESX_HOST | 9.1.0.0.25370933 | VMware-VMvisor-Installer..."
        parts = line.split('|')
        if len(parts) >= 3:
            components.append({
                'component': parts[0].strip(),
                'version': parts[1].strip(),
                'filename': parts[2].strip() if len(parts) > 2 else ''
            })
    
    return {
        'success': True,
        'query': {
            'vcf_version': vcf_version,
            'download_type': download_type,
            'component': component
        },
        'results': components,
        'count': len(components),
    }