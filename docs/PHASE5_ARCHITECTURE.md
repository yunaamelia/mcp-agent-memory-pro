# Phase 5: Advanced Intelligence & Ecosystem

## Overview

Phase 5 introduces Machine Learning capabilities and expands the ecosystem with IDE and Browser extensions.
This transforms the memory system from a passive store to an active, intelligent agent that can predict
importance, tag content automatically, and suggest next tasks.

## 1. Machine Learning Engine

Located in `python/ml/` and `python/predictive/`.

### Importance Predictor

* **Model**: Gradient Boosting Regressor (sklearn/xgboost).
* **Features**: Content length, source reliability, usage patterns, recency.
* **Function**: Predicts an `importance_score` (0-1) for new memories.

### Auto-Tagger

* **Technique**: Keyword extraction + Simple NLP + History-based learning.
* **Function**: Automatically assigns tags based on content (e.g., "python", "bug", "react").

### Task Predictor

* **Technique**: Pattern matching (Temporal, Sequential).
* **Function**: Suggests next tasks based on current context and history.

## 2. Ecosystem Extensions

Scaffolding provided for integration.

### VSCode Extension

* **Commands**: `Save Selection`, `Search Memories`.
* **Integration**: Connects to REST API (`http://localhost:8000`).

### Browser Extension

* **Features**: Popup to save current page, Context menu to save selection.
* **Integration**: Connects to REST API.

## 3. MCP Tools

New tools exposed to the agent.

| Tool | Description |
|Args|
|---|---|
| `memory_predict` | Predict importance or next tasks. | `action`: "importance"\|"next_tasks", `context` |
| `memory_automate` | Trigger auto-tagging or cleanup. | `action`: "auto_tag"\|"cleanup" |

## 4. Automation Workflows

* **Auto-Tagging**: Can be run periodically via `memory_automate` or triggered on new memory insertion (future).
* **Lifecycle Management**: `cleanup` action placeholder for archiving old low-importance memories.

## Verification

* Run `tests/validation/phase5-validate.sh` to verify ML models and Tools.
* See `tests/validation/test-phase5-tools.ts` for usage examples.
