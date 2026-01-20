import os
from pathlib import Path

# Model configuration
MODEL_NAME = os.getenv('EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2')
CACHE_DIR = Path(__file__).parent / 'models'

# Server configuration
HOST = os.getenv('EMBEDDING_HOST', '127.0.0.1')
PORT = int(os.getenv('EMBEDDING_PORT', '5001'))

# Performance
MAX_BATCH_SIZE = int(os.getenv('MAX_BATCH_SIZE', '32'))
WORKERS = int(os.getenv('WORKERS', '1'))

# Ensure cache directory exists
CACHE_DIR.mkdir(exist_ok=True)
