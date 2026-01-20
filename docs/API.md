# MCP Agent Memory Pro - API Documentation

## MCP Tools

### `memory_store`

Store a new memory in the system.

**Parameters:**

```json
{
  "content": "string (required)",
  "type": "code | command | conversation | note | event (required)",
  "source": "ide | terminal | manual (required)",
  "context": {
    "project": "string (optional)",
    "file_path": "string (optional)",
    "language": "string (optional)",
    "tags": ["string"] (optional)
  },
  "importance":  "low | medium | high | critical (optional, default: medium)"
}
```

**Response:**

```json
{
  "success": true,
  "memory_id": "uuid",
  "type": "note",
  "source": "manual",
  "importance": "medium",
  "timestamp": "2026-01-20T10:30:00.000Z",
  "context": {}
}
```

**Example:**

```json
{
  "content": "async function fetchUser(id) { return await db.users.findById(id); }",
  "type": "code",
  "source": "ide",
  "context": {
    "project": "my-app",
    "file_path":  "src/services/user. ts",
    "language": "typescript",
    "tags": ["database", "async"]
  },
  "importance": "high"
}
```

---

### `memory_search`

Search memories using semantic similarity.

**Parameters:**

```json
{
  "query": "string (required)",
  "filters": {
    "time_range": {
      "start": "ISO 8601 datetime",
      "end": "ISO 8601 datetime"
    },
    "types": ["code", "command", "conversation", "note", "event"],
    "projects": ["string"],
    "min_importance":  0.5,
    "tiers": ["short", "working", "long"]
  },
  "limit": 10,
  "include_related": false
}
```

**Response:**

```json
{
  "results": [
    {
      "id": "uuid",
      "type": "code",
      "content": ".. .",
      "project": "my-app",
      "file_path": "src/services/user.ts",
      "timestamp": "2026-01-20T10:30:00.000Z",
      "importance": 0.75,
      "similarity_score": "0.8542",
      "access_count": 3,
      "tags": ["database", "async"]
    }
  ],
  "count": 1,
  "query": "how to fetch user from database",
  "filters": {}
}
```

**Example:**

```json
{
  "query": "how to handle authentication",
  "filters": {
    "types": ["code"],
    "projects": ["my-app"],
    "min_importance":  0.5
  },
  "limit":  5
}
```

---

## CLI Commands

### Store Memory

```bash
mcp-memory-cli store \
  --content "Your content here" \
  --type note \
  --source manual \
  --project my-project \
  --tags "tag1,tag2" \
  --importance high
```

### Search Memories

```bash
mcp-memory-cli search \
  --query "search query" \
  --limit 10 \
  --types "code,note" \
  --min-importance 0.5
```

### View Statistics

```bash
mcp-memory-cli stats
```

### Health Check

```bash
mcp-memory-cli health
```
