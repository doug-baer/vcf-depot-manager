# Deployment Guide

## Docker Compose (Local/Lab)

### 1. Prepare VCFDT Binary

Download the VCFDT tarball from Broadcom, extract, and place the binary:

`mkdir -p bin`

Extract your downloaded tarball

`tar xzf vcf-download-tool-9.1.0.0100.*.tar.gz`

Copy the binary to bin/

`cp vcf-download-tool bin/vcf-download-tool`

`chmod +x bin/vcf-download-tool`

### 2. Configure

`cp .env.example .env`

Edit .env — especially FLASK_SECRET_KEY, ADMIN_USERNAME, ADMIN_PASSWORD

### 3. (Optional) Prepare TLS Certificates

`mkdir -p certs`

`openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout certs/server.key -out certs/server.crt -subj "/CN=vcf-depot.lab.internal"`

### 4. Launch

`docker compose up -d` 
`docker compose logs -f`

### 5. Access

- Web UI: `https://localhost` (or your host)
- Health: `https://localhost/health`
- Depot files: `https://localhost/depot/files/`


## Kubernetes (future)

### 1. Build and Push Image

`docker build -t your-registry/vcf-depot-manager:latest .` 
`docker push your-registry/vcf-depot-manager:latest`

### 2. Update Manifests

- Update `deployment.yaml` image to your registry path
- Update `secret.yaml` with real credentials
- Update `ingress.yaml` with your domain and TLS secret

### 3. Deploy

`kubectl apply -f deploy/kubernetes/namespace.yaml `
`kubectl apply -f deploy/kubernetes/pvc.yaml`
`kubectl apply -f deploy/kubernetes/secret.yaml` 
`kubectl apply -f deploy/kubernetes/configmap.yaml` # (if separated) 
`kubectl apply -f deploy/kubernetes/deployment.yaml` 
`kubectl apply -f deploy/kubernetes/service.yaml` 
`kubectl apply -f deploy/kubernetes/ingress.yaml`

### 4. Verify

`kubectl -n vcf-depot get pods` 
`kubectl -n vcf-depot port-forward svc/vcf-depot-manager 5000:5000`

Open http://localhost:5000

## Post-Deployment

1. Navigate to the **Token** page and upload your Broadcom download token
2. Go to **Downloads** and trigger an INSTALL download for VCF 9.1.0
3. Monitor the job status — downloads can take several hours depending on bandwidth
4. Once complete, point SDDC Manager to `https://your-host/depot/files/`
