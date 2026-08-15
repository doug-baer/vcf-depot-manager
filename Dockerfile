FROM python:3.11-slim AS base

LABEL maintainer="YOUR_ORG"
LABEL description="VCF Depot Manager - Web UI for VMware Cloud Foundation offline depot management"

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user (but keep ability to write to volumes)
RUN groupadd -r vcfdt && useradd -r -g vcfdt -u 1000 -m -d /home/vcfdt vcfdt

WORKDIR /app

# Install Python dependencies first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY config/ ./config/

# Create directories for persistent volumes
RUN mkdir -p /data/depot /data/tokens /data/logs /opt/vcfdt \
    && chown -R vcfdt:vcfdt /data /app /opt/vcfdt

USER vcfdt

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

CMD ["gunicorn", "-c", "config/gunicorn.conf.py", "app.main:app"]