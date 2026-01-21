# Troubleshooting Guide

## Common Issues

### 1. Embedding Service Not Available

**Error:** `Embedding service is not available`

**Solution:**

```bash
# Start the embedding service
cd python
source venv/bin/activate
uvicorn embedding_service:app --host 127.0.0.1 --port 5001

# Or use the convenience script
./scripts/start-services.sh
```

### 2. Port Already in Use

**Error:** `Address already in use:  127.0.0.1:5001`

**Solution:**

```bash
# Find and kill the process
lsof -ti: 5001 | xargs kill -9

# Or change the port
export EMBEDDING_PORT=5002
```

### 3. Database Locked

**Error:** `database is locked`

**Solution:**

```bash
# Stop all services
./scripts/stop-services.sh

# Remove WAL files
rm data/memories.db-wal data/memories.db-shm

# Restart
./scripts/start-services.sh
```

### 4. Vector Search Returns No Results

**Possible causes:**

- No memories stored yet
- Query too specific
- Filters too restrictive

**Solution:**

```bash
# Check if memories exist
mcp-memory-cli stats

# Try broader search
mcp-memory-cli search --query "general topic" --limit 20
```

### 5. Slow First Embedding

**Issue:** First embedding takes 30-60 seconds

**Explanation:** This is normal - the model is being downloaded (~80MB)

**Solution:** Wait for initial download, subsequent requests will be fast

### 6. TypeScript Build Errors

**Error:** `Cannot find module '@/.. .'`

**Solution:**

```bash
# Clean and rebuild
npm run clean
npm run build
```

### 7. Permission Denied on Scripts

**Error:** `Permission denied: ./scripts/start-services.sh`

**Solution:**

```bash
chmod +x scripts/*.sh
```

## Debugging

### Enable Debug Logging

```bash
export LOG_LEVEL=debug
npm start
```

### Check Service Health

```bash
mcp-memory-cli health
```

### View Logs

```bash
# MCP server logs
tail -f data/mcp-memory.log

# Embedding service logs
tail -f data/embedding-service.log
```

### Inspect Database

```bash
sqlite3 data/memories.db "SELECT * FROM memories LIMIT 5;"
```

## Getting Help

1. Check the logs
2. Run health check
3. Try resetting data: `./scripts/reset-data.sh`
4. Open an issue on GitHub with logs attached
