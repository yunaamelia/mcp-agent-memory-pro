# Cognitive Features Guide

This guide explains how to use the Phase 3 cognitive features in MCP Agent Memory Pro.

## Overview

The cognitive layer provides three main capabilities:

1. **Proactive Context Recall** - Automatically surfaces relevant memories based on current work
2. **Smart Suggestions** - Generates actionable recommendations and detects issues
3. **Advanced Analytics** - Provides graph analysis, pattern detection, and trends

## MCP Tools

### memory_recall_context

Analyzes your current work context and recalls relevant memories without explicit searching.

**Usage:**

```json
{
  "tool": "memory_recall_context",
  "arguments": {
    "project": "my-project",      // Optional: focus on specific project
    "file_path": "src/auth.ts",   // Optional: focus on specific file
    "recent_minutes": 30,         // Optional: context window (default: 30)
    "limit": 10                   // Optional: max memories (default: 10)
  }
}
```

**Response includes:**

- `context`: Current context analysis (active projects, entities, focus)
- `recalled_memories`: Relevant memories with relevance scores
- `suggestions`: Context-aware suggestions

### memory_suggestions

Generates proactive suggestions based on memory patterns.

**Usage:**

```json
{
  "tool": "memory_suggestions",
  "arguments": {
    "project": "my-project",       // Optional: project filter
    "context_type": "debugging",   // Optional: hint current activity
    "limit": 5                     // Optional: max suggestions (default: 5)
  }
}
```

**Response includes:**

- `suggestions`: Prioritized actionable suggestions
- `potential_issues`: Detected problems (TODOs, repeated errors)
- `forgotten_knowledge`: Important memories needing review

### memory_analytics

Provides advanced analytics on memory data.

**Query types:**

| Type | Description |
|------|-------------|
| `graph` | Knowledge graph statistics and central entities |
| `patterns` | Detected recurring patterns |
| `statistics` | Overall memory statistics |
| `trends` | Activity trends over time |
| `entities` | Entity-specific analysis |

**Usage:**

```json
{
  "tool": "memory_analytics",
  "arguments": {
    "query_type": "graph",    // Required: type of analysis
    "project": "my-project",  // Optional: project filter
    "entity": "UserService",  // Optional: for entity queries
    "days": 30,               // Optional: analysis period (default: 30)
    "limit": 10               // Optional: max results (default: 10)
  }
}
```

## Python API

For direct Python usage:

```python
from cognitive import (
    GraphQueryEngine,
    ContextAnalyzer,
    SuggestionEngine,
    PatternDetector
)

# Graph analysis
engine = GraphQueryEngine()
central = engine.get_central_entities(top_n=10)
related = engine.find_related_entities("entity_id", max_hops=2)

# Context analysis
analyzer = ContextAnalyzer()
context = analyzer.analyze_current_context()
memories = analyzer.recall_relevant_memories(context)

# Suggestions
suggester = SuggestionEngine()
suggestions = suggester.generate_suggestions()
issues = suggester.detect_potential_issues()

# Patterns
detector = PatternDetector()
patterns = detector.detect_recurring_patterns()
trends = detector.track_trends(project="my-project")
```

## Background Workers

Two workers run automatically:

| Worker | Frequency | Purpose |
|--------|-----------|---------|
| MemoryConsolidator | Daily | Deduplicates and cleans up memories |
| PatternAnalyzer | Hourly | Detects patterns and stores insights |

## Tips

1. **Let context build naturally** - The more you work, the better context recall becomes
2. **Review suggestions regularly** - They surface forgotten but important information
3. **Use analytics for insights** - Graph analysis reveals relationships between concepts
4. **Trust pattern detection** - It identifies recurring workflows and potential issues
