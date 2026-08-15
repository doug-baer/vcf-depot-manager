# Architecture

## Overview

VCF Depot Manager is a Flask web application that wraps the VCF Download Tool (VCFDT)
binary, providing a browser-based interface for managing an offline VCF 9.1 depot.

## Components

┌─────────────────────────────────────────────────────┐
│                 Docker Container                    │
│  ┌─────────────────────────────────────────────┐    │
│  │  Gunicorn (4 workers)                       │    │
│  │  ┌──────────────────────────────────┐       │    │
│  │  │  Flask App (vcf-depot-manager)   │       │    │
│  │  │                                  │       │    │
│  │  │  - Dashboard (/)                 │       │    │
│  │  │  - Depot Browser (/depot/)       │       │    │
│  │  │  - Download Jobs (/downloads)    │       │    │
│  │  │  - Token Mgmt (/token)           │       │    │
│  │  │  - Health (/health)              │       │    │
│  │  └──────────────────────────────────┘       │    │
│  └─────────────────────────────────────────────┘    │
│                       │                             │
│  Volumes (persistent, outside container):           │
│  ┌────────────┐ ┌─────────────┐ ┌────────────┐      │
│  │ /data/depot│ │ /data/tokens│ │ /data/logs │      │
│  └─────┬──────┘ └─────────────┘ └────────────┘      │
│        │                                            │
│  Binary mount:                                      │
│  ┌───────────────────────┐                          │
│  │ /opt/vcfdt/vcfdt-tool │ (read-only host mount)   │
│  └───────────────────────┘                          │
└─────────────────────────────────────────────────────┘
         │
         ▼
   NGINX (TLS termination, depot file serving)
         │
         ▼
   SDDC Manager / vRSLCM consumers


## Data Flow

1. **Token Upload**: Admin uploads Broadcom token via `/token` → saved to `/data/tokens/active_token.txt`
2. **Download Trigger**: Admin clicks "Start Download" → Flask spawns VCFDT subprocess → logs to `/data/logs/`
3. **VCFDT Execution**: Binary writes ISO/OVA/tar.gz files to `/data/depot/COMP/*`
4. **Consumption**: SDDC Manager hits `https://host/depot/files/COMP/...` to pull binaries

## Persistent Volumes

| Volume       | Mount          | Purpose                     | Size   |
|--------------+----------------+-----------------------------+--------|
| `depot_data` | `/data/depot`  | All downloaded VCF binaries | 500Gi+ |
| `token_data` | `/data/tokens` | Active + backed-up tokens   | 1Gi    |
| `log_data`   | `/data/logs`   | Gunicorn + job logs         | 10Gi   |
└--------------+----------------+-----------------------------+--------┘

