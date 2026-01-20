# Deployment Guide

## Production Deployment Options

### Option 1: Docker Compose (Recommended)

```bash
# Build and start
cd deployment/docker
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### Option 2: Kubernetes

```bash
# Apply deployment
kubectl apply -f deployment/kubernetes/deployment.yaml

# Check status
kubectl get pods -n mcp-memory

# View logs
kubectl logs -f deployment/mcp-memory -n mcp-memory
```

### Option 3: SystemD Service

```bash
# Install
sudo cp deployment/systemd/mcp-memory.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable mcp-memory
sudo systemctl start mcp-memory

# Check status
sudo systemctl status mcp-memory
```

### Option 4: Manual Deployment

```bash
# Install dependencies
npm install
cd python && python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-workers.txt
pip install -r requirements-cognitive.txt
pip install -r requirements-phase4.txt

# Build
npm run build

# Start services
./scripts/start-services.sh
./scripts/start-workers.sh

# Start MCP server
node dist/index.js
```

## Environment Variables

```bash
# Required
MCP_MEMORY_DATA_DIR=/app/data

# Optional
LOG_LEVEL=info
WORKERS_ENABLED=true
CLAUDE_API_KEY=your-key-here

# API (Phase 4)
API_HOST=127.0.0.1
API_PORT=8000
```

## Backup Strategy

```bash
# Daily backups
./scripts/backup.sh

# Automated backups (cron)
0 2 * * * /opt/mcp-agent-memory-pro/scripts/backup.sh
```

## Monitoring

```bash
# Health check
curl http://localhost:8000/health

# Worker status
./scripts/monitor-workers.sh

# View logs
tail -f data/mcp-memory. log
tail -f data/worker_manager.log
```

## Scaling Considerations

- **Storage**: Plan for ~1MB per 1000 memories
- **Memory**: Minimum 512MB RAM, recommend 2GB
- **CPU**: 2+ cores recommended for workers
- **Network**: REST API can be load-balanced

## Security Checklist

- [ ] Set API_KEY environment variable
- [ ] Use HTTPS for REST API
- [ ] Restrict file permissions (chmod 600 data/)
- [ ] Regular backups
- [ ] Monitor logs for anomalies
- [ ] Keep dependencies updated
