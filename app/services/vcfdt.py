import os
import subprocess
import threading
import json
from pathlib import Path
from datetime import datetime


class VCFDTService:
    """Wraps the VCF Download Tool (VCFDT) binary for subprocess execution."""

    def __init__(self):
        self.binary = os.environ.get('VCFDT_BIN_PATH', '/opt/vcfdt/vcf-download-tool')
        self.depot_store = os.environ.get('DEPOT_STORE', '/data/depot')
        self.token_dir = os.environ.get('TOKEN_DIR', '/data/tokens')
        self.log_dir = os.environ.get('LOG_DIR', '/data/logs')
        self.vcf_version = os.environ.get('VCF_VERSION', '9.1.0')
        self.sku = os.environ.get('VCF_SKU', 'VCF')

        # Active jobs: {job_id: {"pid": int, "log_file": str, "started_at": str}}
        self._jobs = {}
        self._lock = threading.Lock()

    @property
    def active_token_file(self):
        """Returns the path to the currently active token file."""
        token_path = os.path.join(self.token_dir, 'active_token.txt')
        return token_path

    def list_binaries(self, vcf_version=None, download_type='INSTALL', component=None):
        """List available binaries from Broadcom depot."""
        cmd = [
            self.binary, 'binaries', 'list',
            f'--vcf-version={vcf_version or self.vcf_version}',
            f'--sku={self.sku}',
            f'--type={download_type}',
        ]
        if component:
            cmd.append(f'--component={component}')

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            raise RuntimeError(f'VCFDT list failed: {result.stderr}')
        return result.stdout.strip().split('\n')

    def start_download(self, vcf_version=None, download_type='INSTALL',
                       component=None, patches_only=False, component_version=None):
        """Start a VCFDT download in the background."""
        job_id = f"dl_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        log_file = os.path.join(self.log_dir, f'{job_id}.log')

        cmd = [
            self.binary, 'binaries', 'download',
            f'--depot-download-token-file={self.active_token_file}',
            f'--depot-store={self.depot_store}',
            f'--vcf-version={vcf_version or self.vcf_version}',
            f'--sku={self.sku}',
            f'--type={download_type}',
        ]
        if component:
            cmd.append(f'--component={component}')
        if patches_only:
            cmd.append('--patches-only')
        if component_version:
            cmd.append(f'--component-version={component_version}')

        def _run_job():
            with open(log_file, 'w') as lf:
                proc = subprocess.Popen(
                    cmd, stdout=lf, stderr=subprocess.STDOUT,
                    universal_newlines=True
                )
                with self._lock:
                    self._jobs[job_id] = {
                        'pid': proc.pid,
                        'log_file': log_file,
                        'started_at': datetime.now().isoformat(),
                        'command': ' '.join(cmd),
                    }
                proc.wait()
                with self._lock:
                    if job_id in self._jobs:
                        self._jobs[job_id]['finished_at'] = datetime.now().isoformat()
                        self._jobs[job_id]['returncode'] = proc.returncode

        thread = threading.Thread(target=_run_job, daemon=True)
        thread.start()
        return job_id

    def get_job_status(self, job_id):
        """Return status info for a given job."""
        with self._lock:
            job = self._jobs.get(job_id)
        if not job:
            return {'status': 'not_found'}

        log_content = ''
        if os.path.exists(job['log_file']):
            with open(job['log_file']) as f:
                log_content = f.read()[-3000:]

        if 'returncode' in job:
            status = 'completed' if job['returncode'] == 0 else 'failed'
        else:
            # Check if process is still running
            try:
                os.kill(job['pid'], 0)
                status = 'running'
            except OSError:
                status = 'terminated'

        return {
            'status': status,
            'started_at': job.get('started_at'),
            'finished_at': job.get('finished_at'),
            'returncode': job.get('returncode'),
            'command': job.get('command'),
            'logs': log_content,
        }

    def list_jobs(self):
        """List all known jobs."""
        with self._lock:
            return {jid: {k: v for k, v in j.items() if k != 'log_file'}
                    for jid, j in self._jobs.items()}

    def save_token(self, token_content):
        """Save a new download token, making it the active token."""
        os.makedirs(self.token_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = os.path.join(self.token_dir, f'token_{timestamp}.bak')

        # Backup existing token if present
        if os.path.exists(self.active_token_file):
            os.rename(self.active_token_file, backup_path)

        with open(self.active_token_file, 'w') as f:
            f.write(token_content.strip())

        return self.active_token_file

    def has_active_token(self):
        return os.path.isfile(self.active_token_file)


vcfdt_service = VCFDTService()