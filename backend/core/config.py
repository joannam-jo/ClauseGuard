"""Core configuration settings."""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Database
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'test_database')

# CORS
CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*')

# Environment
IS_PRODUCTION = os.environ.get('IS_PRODUCTION', 'false').lower() == 'true'

# LLM
LLM_API_KEY = os.environ.get('LLM_API_KEY')
LLM_PROVIDER = os.environ.get('LLM_PROVIDER', 'openai')
LLM_MODEL = os.environ.get('LLM_MODEL', 'gpt-4o')
LLM_BASE_URL = os.environ.get('LLM_BASE_URL')  # Optional: custom base URL (e.g. Groq)
OLLAMA_BASE_URL = os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434')
OLLAMA_TIMEOUT = int(os.environ.get('OLLAMA_TIMEOUT', '300'))
OLLAMA_NUM_PREDICT = int(os.environ.get('OLLAMA_NUM_PREDICT', '256'))
# Default clamping: keep prompts reasonably small to improve latency and avoid timeouts
OLLAMA_MAX_ANALYSIS_CHARS = int(os.environ.get('OLLAMA_MAX_ANALYSIS_CHARS', '3000'))
OLLAMA_MAX_CLAUSE_CHARS = int(os.environ.get('OLLAMA_MAX_CLAUSE_CHARS', '3000'))
OLLAMA_MAX_CHAT_CHARS = int(os.environ.get('OLLAMA_MAX_CHAT_CHARS', '2000'))

# OAuth
OAUTH_SESSION_URL = os.environ.get('OAUTH_SESSION_URL')

# Directories
BACKEND_DIR = Path(__file__).resolve().parent.parent

# Vector Store
CHROMA_PERSIST_DIR = os.environ.get('CHROMA_PERSIST_DIR', str(BACKEND_DIR / 'chroma_db'))

# Model Cache
MODEL_CACHE_DIR = str(BACKEND_DIR / 'model_cache')
os.environ['HF_HOME'] = MODEL_CACHE_DIR
os.environ['TRANSFORMERS_CACHE'] = MODEL_CACHE_DIR

# File Upload
UPLOAD_DIR = BACKEND_DIR / 'uploads'
UPLOAD_DIR.mkdir(exist_ok=True)

# ML Models Directory
ML_MODELS_DIR = BACKEND_DIR / 'ml_models'
ML_MODELS_DIR.mkdir(exist_ok=True)

# JWT Settings
JWT_SECRET = os.environ.get('JWT_SECRET', 'finance-analyzer-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRE_HOURS = 168  # 7 days
