# API Reference

## Endpoints

### GET /health
Unauthenticated health check for container probes.

json { "status": "healthy", "vcfdt_binary": true, "depot_exists": true, "has_token": true }

### POST /downloads/start
Start a VCFDT download job. Requires Basic Auth.

json // Request (form-encoded) { "vcf_version": "9.1.0", "download_type": "INSTALL", "component": "ESX_HOST", "patches_only": "on", "component_version": "9.1.0.0400" }

### GET /downloads/status/{job_id}
Check job status. Requires Basic Auth.

json { "status": "running", "started_at": "2026-08-15T10:30:00", "logs": "..." }

### POST /token
Upload a new download token file (multipart form). Requires Basic Auth.

Form field: token_file (file upload)

### GET /depot/files/{path}
Serve depot files. No auth (consumed by SDDC Manager / vRSLCM).
Protected at network layer.