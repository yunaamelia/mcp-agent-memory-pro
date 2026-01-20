# ============================================================================
# MCP Agent Memory Pro - Dockerfile
# ============================================================================

FROM node:20-slim AS builder

# Install Python
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy package files
COPY package*.json ./
COPY tsconfig.json ./

# Install Node dependencies
RUN npm ci

# Copy source
COPY src/ ./src/
COPY python/ ./python/

# Build TypeScript
RUN npm run build

# Setup Python environment
RUN cd python && \
    python3 -m venv venv && \
    .  venv/bin/activate && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r requirements-workers.txt && \
    pip install --no-cache-dir -r requirements-cognitive.txt && \
    pip install --no-cache-dir -r requirements-phase4.txt && \
    python3 -m spacy download en_core_web_sm

# ============================================================================
# Production image
# ============================================================================

FROM node:20-slim

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy built files
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/python ./python
COPY --from=builder /app/package*.json ./

# Copy scripts
COPY scripts/ ./scripts/

# Create data directory
RUN mkdir -p /app/data /app/data/vectors /app/data/exports /app/data/worker_logs

# Expose ports
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Start services
CMD ["sh", "-c", "./scripts/start-services.sh && ./scripts/start-workers.sh && node dist/index.js"]
