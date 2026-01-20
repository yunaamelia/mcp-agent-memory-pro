
import logging
import sqlite3

import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db():
    """Initialize database tables"""
    logger.info(f"Initializing database at {config.DB_PATH}")

    # Ensure directory exists
    config.DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(config.DB_PATH)

    try:
        # Memories table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                content TEXT,
                type TEXT,
                tier TEXT,
                project TEXT,
                importance_score REAL,
                access_count INTEGER DEFAULT 0,
                timestamp INTEGER,
                entities TEXT,
                archived INTEGER DEFAULT 0
            )
        ''')

        # Entities table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS entities (
                name TEXT,
                type TEXT,
                mention_count INTEGER,
                PRIMARY KEY (name, type)
            )
        ''')

        # Entity Relationships table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS entity_relationships (
                source TEXT,
                target TEXT,
                type TEXT,
                UNIQUE(source, target, type)
            )
        ''')

        # Statistics table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS statistics (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')

        conn.commit()
        logger.info("Database initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    init_db()
