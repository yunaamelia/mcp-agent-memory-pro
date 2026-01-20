# Phase 5: Ecosystem & Advanced Intelligence

This phase introduces major ecosystem expansions and backend intelligence features to MCP Agent Memory Pro.

## 1. Extensions

### VSCode Extension

**Location:** `extensions/vscode/`
The VSCode extension integrates Agent Memory directly into the IDE.

- **Commands:**
  - `MCP Memory: Search Memories` (Ctrl+Shift+M)
  - `MCP Memory: Store Selection` (Ctrl+Shift+S)
  - `MCP Memory: Recall Context`
- **Views:**
  - **Memories Tree:** Shows recent memories.
  - **Suggestions:** Proactive code suggestions based on context.

**Setup:**

1. `cd extensions/vscode`
2. `npm install`
3. Press F5 to debug or `npm run compile` to build.

### Browser Extension

**Location:** `extensions/browser/`
A Manifest V3 Chrome extension for capturing web context.

- **Features:**
  - Save current page as memory.
  - Right-click context menu to save selected text.
  - Search memories via popup.
  - Dashboard quick link.

**Installation:**

1. Open `chrome://extensions`
2. Enable Developer Mode.
3. Click "Load Unpacked" and select `extensions/browser/`.

## 2. Plugin System

**Location:** `python/plugins/`
The plugin system allows extending the backend without modifying core files.

- **Structure:** Each plugin is a directory with a `plugin.json` manifest and `index.py`.
- **Hooks:**
  - `before_store(memory_data)`: Modify memory before saving (e.g., auto-tagging).
  - `after_search(query, results)`: Filter or rank search results.

**Creating a Plugin:**
See `python/plugins/example-plugin/` for a reference implementation.

## 3. Advanced Backend

### Caching

**Location:** `python/services/caching_service.py`
Implements LRU (Least Recently Used) caching with TTL (Time To Live) support. Used to optimize:

- Frequent memory queries.
- Dashboard analytics data.

### New API Endpoints

**Location:** `python/api/routes/advanced.py`
New endpoints powered by the advanced services:

- `POST /api/v1/predict`: Predict next user actions.
- `POST /api/v1/automate`: Trigger automated tasks.
- `GET /api/v1/profile/{id}`: Get entity knowledge graph profile.

## 4. Verification

Run the validation suite to ensure all components are active:

```bash
python scripts/validate_phase5.py
```

Run unit tests:

```bash
pytest tests/phase5/
```
