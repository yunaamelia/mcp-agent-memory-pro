import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = Path(os.getenv("MCP_MEMORY_DATA_DIR", BASE_DIR / "data"))
DB_PATH = DATA_DIR / "memories.db"

# Embedding Service (Phase 1)
MODEL_NAME = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
CACHE_DIR = Path(__file__).parent / "models"
HOST = os.getenv("EMBEDDING_HOST", "127.0.0.1")
PORT = int(os.getenv("EMBEDDING_PORT", "5001"))

# Worker Configuration (Phase 2)
WORKERS_ENABLED = os.getenv("WORKERS_ENABLED", "true").lower() == "true"
WORKER_LOG_DIR = DATA_DIR / "worker_logs"
WORKER_LOG_DIR.mkdir(exist_ok=True)

# Claude API
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022")
CLAUDE_MAX_TOKENS = int(os.getenv("CLAUDE_MAX_TOKENS", "1024"))

# Memory Tiers (days)
SHORT_TERM_DAYS = int(os.getenv("SHORT_TERM_DAYS", "2"))
WORKING_TERM_DAYS = int(os.getenv("WORKING_TERM_DAYS", "30"))

# Importance Scoring
IMPORTANCE_SCORE_THRESHOLD = float(os.getenv("IMPORTANCE_SCORE_THRESHOLD", "0.7"))
MIN_ACCESS_COUNT_FOR_PROMOTION = int(os.getenv("MIN_ACCESS_COUNT_FOR_PROMOTION", "2"))

# Entity Extraction
NER_MODEL = os.getenv("NER_MODEL", "en_core_web_sm")
ENTITY_CONFIDENCE_THRESHOLD = float(os.getenv("ENTITY_CONFIDENCE_THRESHOLD", "0.5"))

# Summarization
SUMMARIZATION_BATCH_SIZE = int(os.getenv("SUMMARIZATION_BATCH_SIZE", "10"))
MAX_SUMMARY_LENGTH = int(os.getenv("MAX_SUMMARY_LENGTH", "500"))

# Job Scheduling (cron expressions)
SCHEDULE_IMPORTANCE_SCORER = os.getenv("SCHEDULE_IMPORTANCE_SCORER", "*/5 * * * *")  # Every 5 min
SCHEDULE_ENTITY_EXTRACTOR = os.getenv("SCHEDULE_ENTITY_EXTRACTOR", "*/15 * * * *")  # Every 15 min
SCHEDULE_MEMORY_PROMOTER = os.getenv("SCHEDULE_MEMORY_PROMOTER", "0 * * * *")  # Hourly
SCHEDULE_SUMMARIZER = os.getenv("SCHEDULE_SUMMARIZER", "0 2 * * *")  # Daily at 2 AM
SCHEDULE_GRAPH_BUILDER = os.getenv("SCHEDULE_GRAPH_BUILDER", "0 3 * * *")  # Daily at 3 AM

# Performance
MAX_WORKERS = int(os.getenv("MAX_WORKERS", "4"))
BATCH_SIZE = int(os.getenv("WORKER_BATCH_SIZE", "50"))

# Ensure cache and log directories exist
CACHE_DIR.mkdir(exist_ok=True)
WORKER_LOG_DIR.mkdir(exist_ok=True)
