# Workers Guide

## Quick Start

```bash
# Start all workers
npm run workers:start

# Stop all workers
npm run workers:stop

# Monitor health
npm run workers:monitor
```

## Individual Workers

Run a specific worker manually:

```bash
source .venv/bin/activate

# Run importance scorer
python python/workers/importance_scorer.py

# Run entity extractor
python python/workers/entity_extractor.py

# Run memory promoter
python python/workers/memory_promoter.py

# Run summarizer (requires CLAUDE_API_KEY)
python python/workers/summarizer.py

# Run graph builder
python python/workers/graph_builder.py
```

## Customizing Schedules

Edit `.env`:

```bash
# Run every 10 minutes instead of 5
SCHEDULE_IMPORTANCE_SCORER=*/10 * * * *

# Run twice daily
SCHEDULE_SUMMARIZER=0 2,14 * * *
```

Cron format: `minute hour day month weekday`

## Disabling Workers

```bash
# In .env
WORKERS_ENABLED=false
```

## Viewing Results

### Via MCP Tool

In Claude Desktop:
> "Show me memory health insights"
> "What are the top entities in my memories?"

### Via CLI (planned)

```bash
mcp-memory-cli insights overview
mcp-memory-cli insights entities
mcp-memory-cli insights health
```
