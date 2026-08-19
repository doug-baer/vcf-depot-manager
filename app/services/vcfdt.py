import os
import subprocess
import threading
import uuid
from pathlib import Path
from datetime import datetime

class VCFDTService:
    """Wraps the VCF Download Tool (VCFDT) binary for subprocess execution."""

    def __init__(self):
        self.binary = os.environ.get('VCFDT_BIN_PATH', '/opt/vcfdt/bin/vcf-download-tool')
        self.depot_store = os.environ.get('DEPOT_STORE', '/data/depot')
        self.token_dir = os.environ.get('TOKEN_DIR', '/data/tokens')
        self.log_dir = os.environ.get('LOG_DIR', '/data/logs')
        self.vcf_version = os.environ.get('VCF_VERSION', '9.1.0')
        self.sku = os.environ.get('VCF_SKU', 'VCF')

        # Ensure directories exist
        os.makedirs(self.token_dir, exist_ok=True)
        os.makedirs(self.log_dir, exist_ok=True)
        os.makedirs(self.depot_store, exist_ok=True)

        # Job registry: {job_id: {...}}
        self._jobs = {}
        self._lock = threading.Lock()

        # Load persisted jobs on startup (from previous sessions)
        self._load_persisted_jobs()

    # ─── Depot ID ───────────────────────────────────────────

    @property
    def depot_id_file(self):
        return os.path.join(self.token_dir, 'software-depot-id.txt')

    def generate_depot_id(self):
        """Run VCFDT to generate a new Software Depot ID and extract the UUID."""
        import re

        cmd = [self.binary, 'configuration', 'generate', '--software-depot-id']

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            # VCFDT prints a welcome message with a registration link.
            # Extract the UUID that follows "serviceId="
            output = result.stdout.strip()
            match = re.search(r'serviceId=([a-f0-9\-]+)', output, re.IGNORECASE)

            if match:
                depot_id = match.group(1)

                # Write the clean UUID to persistent storage
                with open(self.depot_id_file, 'w') as f:
                    f.write(depot_id)

                return {
                    'success': True,
                    'depot_id': depot_id,
                    'full_output': output,
                    'stderr': result.stderr.strip(),
                    'returncode': result.returncode,
                    'saved_to': self.depot_id_file,
                }
            else:
                # Could not find serviceId in output
                return {
                    'success': False,
                    'depot_id': None,
                    'full_output': output,
                    'stderr': result.stderr.strip(),
                    'returncode': result.returncode,
                    'error': 'Could not parse serviceId from command output',
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'full_output': '',
                'stderr': str(e),
                'returncode': -1,
            }

    def get_depot_id(self):
        """Read the stored depot ID from disk, if it exists."""
        if os.path.isfile(self.depot_id_file):
            with open(self.depot_id_file) as f:
                return f.read().strip()
        return None

    def has_depot_id(self):
        return self.get_depot_id() is not None

    # ─── Activation Code (VCF 9.1 replaces download token) ─

    @property
    def activation_code_file(self):
        return os.path.join(self.token_dir, 'activation-code.txt')

    def save_activation_code(self, code_content):
        """Save a Broadcom activation code (returned after registering the depot ID)."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = os.path.join(self.token_dir, f'activation-code_{timestamp}.bak')

        if os.path.exists(self.activation_code_file):
            os.rename(self.activation_code_file, backup_path)

        with open(self.activation_code_file, 'w') as f:
            f.write(code_content.strip())

        return self.activation_code_file

    def has_activation_code(self):
        return os.path.isfile(self.activation_code_file)

    def get_activation_code(self):
        if os.path.isfile(self.activation_code_file):
            with open(self.activation_code_file) as f:
                return f.read().strip()
        return None

    # ─── Legacy token support (backwards compat) ────────────

    @property
    def active_token_file(self):
        """For backwards compat — tries activation code first, then legacy token."""
        if self.has_activation_code():
            return self.activation_code_file
        legacy_token = os.path.join(self.token_dir, 'active_token.txt')
        if os.path.exists(legacy_token):
            return legacy_token
        return self.activation_code_file

    def has_active_token(self):
        return self.has_activation_code() or os.path.isfile(
            os.path.join(self.token_dir, 'active_token.txt'))

    def save_token(self, token_content):
        """Legacy method — redirects to activation code storage for VCF 9.1."""
        return self.save_activation_code(token_content)

    # ─── List Binaries ──────────────────────────────────────

    def list_binaries(self, vcf_version=None, download_type='INSTALL', component=None):
        """List available binaries. Runs synchronously (fast command)."""
        cmd = [
            self.binary, 'binaries', 'list',
            f'--vcf-version={vcf_version or self.vcf_version}',
            f'--sku={self.sku}',
            f'--type={download_type}',
        ]
        if component:
            cmd.append(f'--component={component}')

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

            return {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode,
                'command': ' '.join(cmd),
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'stdout': '',
                'stderr': str(e),
                'returncode': -1,
                'command': ' '.join(cmd),
            }

    # ─── Job Management (Fixed) ─────────────────────────────

    def start_download_job(self, vcf_version=None, download_type='INSTALL',
                           component=None, patches_only=False, component_version=None):
        """Start a VCFDT download in the background with proper job tracking."""
        job_id = f"dl_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
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

        return self._spawn_job(job_id, 'download', cmd, log_file)

    def start_esx_configuration_job(self, excluded_versions=None):
        """Configure ESX patch store filtering (common pre-download task)."""
        job_id = f"esx_cfg_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        log_file = os.path.join(self.log_dir, f'{job_id}.log')

        cmd = [
            self.binary, 'esx', 'configuration',
            '-G',  # Global setting
        ]
        if excluded_versions:
            for ver in excluded_versions:
                cmd.append(f'-D={ver}')

        return self._spawn_job(job_id, 'esx_configuration', cmd, log_file)

    def _spawn_job(self, job_id, job_type, cmd, log_file):
        """Internal method to spawn a background job with proper tracking."""

        # Initialize job record immediately (thread-safe)
        with self._lock:
            self._jobs[job_id] = {
                'job_id': job_id,
                'type': job_type,
                'command': ' '.join(cmd),
                'started_at': datetime.now().isoformat(),
                'finished_at': None,
                'returncode': None,
                'status': 'starting',  # starting → running → completed/failed
                'log_file': log_file,
                'pid': None,
            }

        def _run():
            try:
                # Open log file for writing
                with open(log_file, 'w') as lf:
                    # Start the process
                    proc = subprocess.Popen(
                        cmd,
                        stdout=lf,
                        stderr=subprocess.STDOUT,
                        universal_newlines=True,
                        bufsize=1
                    )

                    # Update job status to running and store PID
                    with self._lock:
                        self._jobs[job_id]['status'] = 'running'
                        self._jobs[job_id]['pid'] = proc.pid

                    # Wait for completion
                    proc.wait()
                    exit_code = proc.returncode

                # Mark as finished
                with self._lock:
                    self._jobs[job_id]['status'] = 'completed' if exit_code == 0 else 'failed'
                    self._jobs[job_id]['finished_at'] = datetime.now().isoformat()
                    self._jobs[job_id]['returncode'] = exit_code

            except Exception as e:
                with self._lock:
                    self._jobs[job_id]['status'] = 'failed'
                    self._jobs[job_id]['finished_at'] = datetime.now().isoformat()
                    self._jobs[job_id]['error'] = str(e)

        # Spawn the thread
        thread = threading.Thread(target=_run, daemon=True)
        thread.start()

        return job_id

    # ─── Job Query Methods ─────────────────────────────────

    def get_job_status(self, job_id):
        """Return status info for a given job."""
        with self._lock:
            job = self._jobs.get(job_id)

        if not job:
            return {'status': 'not_found', 'message': f'Job {job_id} not found'}

        # Read recent logs
        log_content = ''
        if os.path.exists(job['log_file']):
            with open(job['log_file']) as f:
                lines = f.readlines()
                log_content = ''.join(lines[-100:])  # Last 100 lines

        return {
            'job_id': job['job_id'],
            'type': job['type'],
            'status': job['status'],
            'started_at': job['started_at'],
            'finished_at': job['finished_at'],
            'returncode': job['returncode'],
            'command': job['command'],
            'pid': job['pid'],
            'logs_tail': log_content,
        }

    def list_jobs(self):
        """List all known jobs."""
        with self._lock:
            return {jid: {k: v for k, v in j.items() if k != 'log_file'}
                    for jid, j in self._jobs.items()}

    def get_last_job_output(self, job_type=None):
        """Get the output from the most recent job of a given type."""
        with self._lock:
            jobs = self._jobs.copy()

        if job_type:
            filtered = {k: v for k, v in jobs.items() if v['type'] == job_type}
            if not filtered:
                return None
            job_id = max(filtered.keys(), key=lambda k: filtered[k]['started_at'])
        else:
            if not jobs:
                return None
            job_id = max(jobs.keys(), key=lambda k: jobs[k]['started_at'])

        job = jobs.get(job_id)
        if not job:
            return None

        log_content = ''
        if os.path.exists(job['log_file']):
            with open(job['log_file']) as f:
                log_content = f.read()

        return {
            'job_id': job_id,
            'type': job['type'],
            'status': job['status'],
            'output': log_content,
            'returncode': job['returncode'],
        }

    # ─── Persistence (save/load jobs across restarts) ───────

    def _persist_jobs(self):
        """Save job state to disk."""
        import json
        import pickle
        state_file = os.path.join(self.log_dir, '.job_state.pkl')
        with open(state_file, 'wb') as f:
            pickle.dump(self._jobs, f)

    def _load_persisted_jobs(self):
        """Load job state from disk on startup."""
        import pickle
        state_file = os.path.join(self.log_dir, '.job_state.pkl')
        if os.path.exists(state_file):
            try:
                with open(state_file, 'rb') as f:
                    loaded_jobs = pickle.load(f)
                with self._lock:
                    self._jobs.update(loaded_jobs)
            except Exception:
                pass  # Start fresh if unpickle fails

# Singleton instance
vcfdt_service = VCFDTService()

