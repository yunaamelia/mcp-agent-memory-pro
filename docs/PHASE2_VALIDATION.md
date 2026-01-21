# Phase 2 Validation Guide

## Quick Start

```bash
# Full Phase 2 validation
npm run validate:phase2

# Or directly
./tests/validation/phase2-validate.sh
```

## Prerequisites

- ✅ Phase 1 validated
- ✅ Python 3.10+ with venv
- ✅ Node.js 20+
- ✅ Embedding service running

## Individual Test Components

| Test        | Command                           | What it Tests               |
| ----------- | --------------------------------- | --------------------------- |
| Services    | `npm run test:services`           | Scoring, NER, Summarization |
| Workers     | `npm run test:workers`            | All 5 workers               |
| Scheduler   | `npm run test:scheduler`          | Job scheduling, lifecycle   |
| Insights    | `npm run test:insights`           | memory_insights MCP tool    |
| Integration | `npm run test:worker-integration` | End-to-end workflows        |
| Performance | `npm run test:worker-perf`        | Benchmarks                  |

## Performance Targets

| Worker            | Target | Acceptable |
| ----------------- | ------ | ---------- |
| Importance Scorer | < 5s   | < 10s      |
| Entity Extractor  | < 10s  | < 15s      |
| Memory Promoter   | < 3s   | < 5s       |
| Graph Builder     | < 5s   | < 10s      |

## Success Criteria

Phase 2 passes when:

- ✅ All intelligence services functional
- ✅ All 5 workers execute without errors
- ✅ Scheduler starts, schedules jobs, and stops
- ✅ Insights tool returns all insight types
- ✅ Performance within acceptable limits

## Troubleshooting

### Workers fail to initialize

```bash
cd python && source venv/bin/activate
pip install -r requirements-workers.txt
```

### Summarization tests skip

Add Claude API key:

```bash
export CLAUDE_API_KEY=your-key-here
```

## Validation Report

```bash
cat tests/phase2-validation-report.json | python3 -m json.tool
```
