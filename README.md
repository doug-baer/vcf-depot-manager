# VCF Depot Manager

A lightweight web application for managing a VMware Cloud Foundation (VCF) 9.1 offline depot.
Wraps the VCF Download Tool (VCFDT) in a Flask web UI, running inside a Docker container
with persistent volume mounts for the depot store and token files.

NOTE: in VCF 9.1, "download tokens" have been replaced with Activation Codes
`--depot-download-activation-code-file` instead of `--depot-download-token-file`

## Features

- Dashboard with depot size, component inventory, and job status
- Browse depot contents with directory navigation
- Trigger VCFDT downloads (INSTALL / UPGRADE / patches) from the browser
- Upload and rotate download tokens via the web UI
- Upload files manually for air-gapped transfers
- Health check endpoint for container orchestration
- Basic authentication
- (stretch goal) Kubernetes-ready manifests included

## Quick Start

`git clone...` 

## Configure

`cp .env.example .env`

Edit .env with your settings

## Launch

`docker compose up -d`

Open `http://localhost:5000` (or your configured port).

## Prerequisites

- VCFDT binary downloaded from the Broadcom portal
- A VCF download token from Broadcom
- Docker and Docker Compose (or Podman)

## Architecture

See [docs/architecture.md](docs/architecture.md) for the full design overview.

## Kubernetes Deployment

See [deploy/kubernetes/](deploy/kubernetes/) for manifests and [docs/deployment.md](docs/deployment.md)
for instructions.

## License

MIT