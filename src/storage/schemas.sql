-- ============================================
-- METADATA DATABASE SCHEMA
-- ============================================

-- Main memories table
CREATE TABLE IF NOT EXISTS memories (
    id TEXT PRIMARY KEY,
    tier TEXT NOT NULL DEFAULT 'short',
    type TEXT NOT NULL,
    source TEXT NOT NULL,
    
    -- Content
    content TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    
    -- Metadata
    timestamp INTEGER NOT NULL,
    project TEXT,
    file_path TEXT,
    language TEXT,
    tags TEXT,
    entities TEXT,
    
    -- Intelligence metrics
    importance_score REAL DEFAULT 0.5,
    access_count INTEGER DEFAULT 0,
    last_accessed INTEGER,
    
    -- Lifecycle
    created_at INTEGER NOT NULL,
    promoted_from TEXT,
    archived INTEGER DEFAULT 0,
    
    FOREIGN KEY (promoted_from) REFERENCES memories(id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_memories_timestamp ON memories(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_memories_tier ON memories(tier);
CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(type);
CREATE INDEX IF NOT EXISTS idx_memories_project ON memories(project);
CREATE INDEX IF NOT EXISTS idx_memories_importance ON memories(importance_score DESC);
CREATE INDEX IF NOT EXISTS idx_memories_archived ON memories(archived);
CREATE INDEX IF NOT EXISTS idx_memories_content_hash ON memories(content_hash);

-- Full-text search on content
CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
    id UNINDEXED,
    content,
    content=memories,
    content_rowid=rowid
);

-- Triggers to keep FTS in sync
CREATE TRIGGER IF NOT EXISTS memories_fts_insert AFTER INSERT ON memories BEGIN
    INSERT INTO memories_fts(rowid, id, content) VALUES (new.rowid, new.id, new. content);
END;

CREATE TRIGGER IF NOT EXISTS memories_fts_delete AFTER DELETE ON memories BEGIN
    DELETE FROM memories_fts WHERE rowid = old.rowid;
END;

CREATE TRIGGER IF NOT EXISTS memories_fts_update AFTER UPDATE ON memories BEGIN
    UPDATE memories_fts SET content = new.content WHERE rowid = new. rowid;
END;

-- ============================================
-- GRAPH SCHEMA
-- ============================================

-- Entities (extracted from memories)
CREATE TABLE IF NOT EXISTS entities (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    name TEXT NOT NULL,
    first_seen INTEGER NOT NULL,
    last_seen INTEGER NOT NULL,
    mention_count INTEGER DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(type);
CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(name);

-- Relationships between memories and entities
CREATE TABLE IF NOT EXISTS memory_entities (
    memory_id TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    relevance REAL DEFAULT 1.0,
    PRIMARY KEY (memory_id, entity_id),
    FOREIGN KEY (memory_id) REFERENCES memories(id) ON DELETE CASCADE,
    FOREIGN KEY (entity_id) REFERENCES entities(id) ON DELETE CASCADE
);

-- Relationships between entities (graph edges)
CREATE TABLE IF NOT EXISTS entity_relationships (
    source_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    type TEXT NOT NULL,
    strength REAL DEFAULT 0.5,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL,
    PRIMARY KEY (source_id, target_id, type),
    FOREIGN KEY (source_id) REFERENCES entities(id) ON DELETE CASCADE,
    FOREIGN KEY (target_id) REFERENCES entities(id) ON DELETE CASCADE
);

-- ============================================
-- CONFIGURATION TABLE
-- ============================================

CREATE TABLE IF NOT EXISTS config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at INTEGER NOT NULL
);

-- Insert default configurations
INSERT OR IGNORE INTO config (key, value, updated_at) VALUES
    ('version', '1.0.0', strftime('%s', 'now')),
    ('short_term_days', '2', strftime('%s', 'now')),
    ('working_term_days', '30', strftime('%s', 'now')),
    ('embedding_model', 'all-MiniLM-L6-v2', strftime('%s', 'now')),
    ('embedding_dimensions', '384', strftime('%s', 'now'));

-- ============================================
-- STATISTICS TABLE
-- ============================================

CREATE TABLE IF NOT EXISTS statistics (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at INTEGER NOT NULL
);

-- Insert initial statistics
INSERT OR IGNORE INTO statistics (key, value, updated_at) VALUES
    ('total_memories', '0', strftime('%s', 'now')),
    ('total_searches', '0', strftime('%s', 'now')),
    ('last_cleanup', strftime('%s', 'now'), strftime('%s', 'now'));
